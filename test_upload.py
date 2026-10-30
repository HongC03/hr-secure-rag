"""Upload validation, authenticated HTTP access, and private retrieval checks."""
import io
import time
import unittest
from unittest.mock import MagicMock, patch

from backend.controllers.api_controller import ApiController
from backend.repositories.document_repository import InMemoryDocumentRepository
from backend.repositories.pgvector_repository import PgVectorRepository
from backend.repositories.user_repository import UserRepository
from backend.services.access_service import AccessService
from backend.services.audit_service import AuditService
from backend.services.embedding_service import EmbeddingGemmaEmbedding
from backend.services.rag_service import RagService
from backend.services.security_service import SecurityService
from backend.services.session_service import SessionService
from backend.services.upload_service import UploadService
from seed.demo_data import USERS

with patch.object(PgVectorRepository, "from_environment", return_value=MagicMock()), patch.object(UserRepository, "from_environment", return_value=MagicMock()):
    from backend.server import HRHandler


def account(user_id="alice"):
    return {"id": user_id, **USERS[user_id]}


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.vectors = MagicMock()
        self.vectors.personal_documents.return_value = []
        self.documents = InMemoryDocumentRepository([])
        self.rag = RagService(AccessService(), self.vectors)
        self.sessions = SessionService(USERS)
        self.controller = ApiController(USERS, self.documents, self.sessions, self.rag, SecurityService(), AuditService())

    def test_every_authenticated_role_can_upload_with_trusted_owner(self):
        for user_id in USERS:
            with self.subTest(user_id=user_id):
                response = self.controller.upload(account(user_id), "policy.MD", b"Synthetic leave policy.", time.perf_counter())
                self.assertEqual(response.status, 201)
                chunks = self.vectors.upsert.call_args.args[0]
                self.assertEqual(chunks[0]["owner_id"], user_id)
                self.assertEqual(chunks[0]["document_type"], "personal_upload")
                self.assertEqual(chunks[0]["classification"], "PRIVATE · UPLOAD")
                self.assertEqual(self.vectors.upsert.call_args.kwargs["user"], account(user_id))

    def test_upload_requires_identity(self):
        self.assertEqual(self.controller.upload(None, "file.txt", b"data", time.perf_counter()).status, 401)
        self.vectors.upsert.assert_not_called()

    def test_invalid_files_are_never_indexed(self):
        cases = [
            ("file.pdf", b"%PDF", 400),
            ("../file.txt", b"text", 400),
            ("C:\\file.txt", b"text", 400),
            ("bad\nfile.txt", b"text", 400),
            ("", b"text", 400),
            ("x" * 201 + ".txt", b"text", 400),
            ("file.txt", b"", 400),
            ("file.txt", b" \n\t", 400),
            ("file.txt", b"\xff", 400),
            ("file.txt", b"binary\x00content", 400),
            ("file.txt", b"x" * (UploadService.MAX_BYTES + 1), 413),
        ]
        for filename, data, status in cases:
            with self.subTest(filename=filename, size=len(data)):
                self.assertEqual(self.controller.upload(account(), filename, data, time.perf_counter()).status, status)
        self.vectors.upsert.assert_not_called()

    def test_unicode_and_bom_text_are_supported(self):
        document = UploadService().build_document("alice", "假期.md", "\ufeff假期政策\nAnnual leave".encode())
        self.assertEqual(document["content"], "假期政策\nAnnual leave")

    def test_failed_upload_returns_generic_error_and_no_source(self):
        self.vectors.upsert.side_effect = RuntimeError("secret database detail")
        response = self.controller.upload(account(), "private.txt", b"private content", time.perf_counter())
        self.assertEqual(response.status, 503)
        self.assertNotIn("secret database detail", str(response.body))
        self.assertEqual(self.documents.all(), [])
        event = self.controller.audit.recent()[-1]
        self.assertEqual(event.outcome, "index_failed")
        self.assertNotIn("private.txt", repr(event))
        self.assertNotIn("private content", repr(event))

    def test_personal_upload_is_private_even_from_hr(self):
        document = UploadService().build_document("alice", "file.txt", b"data")
        for user_id in USERS:
            self.assertEqual(AccessService().can_read(account(user_id), document), user_id == "alice")
        self.assertFalse(AccessService().can_read(account(), {**document, "owner_id": None}))

    def test_persisted_upload_is_retrieved_without_in_memory_source(self):
        document = UploadService().build_document("alice", "leave.txt", b"Annual leave entitlement is 20 days.")
        chunks = self.rag.chunking.chunk_document(document)
        metadata = {key: document[key] for key in ("id", "title", "document_type", "classification", "owner_id")}
        self.vectors.personal_documents.return_value = [metadata]
        self.vectors.search.return_value = chunks
        self.vectors.include_neighbours.side_effect = lambda _user, hits: hits
        with patch.object(EmbeddingGemmaEmbedding, "_get_query_embedding", return_value=[0.0]):
            self.assertEqual(self.rag.retrieve(account(), "Annual leave entitlement", []), chunks)
            self.assertEqual(self.vectors.search.call_args.args[2], [document["id"]])
            self.vectors.search.reset_mock()
            self.assertEqual(self.rag.retrieve(account("priya"), "Annual leave entitlement", []), [])
            self.vectors.search.assert_not_called()

    def test_upload_list_applies_identity_before_database_read(self):
        pool = MagicMock()
        cursor = pool.connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [("upload-1", "leave.txt", "personal_upload", "PRIVATE · UPLOAD", "alice")]
        repository = PgVectorRepository("unused", pool=pool)
        documents = repository.personal_documents(account())
        self.assertEqual(documents[0]["id"], "upload-1")
        self.assertEqual(cursor.execute.call_args_list[0].args[1], ("alice",))
        self.assertEqual(cursor.execute.call_args_list[1].args[1], ("employee",))
        self.assertIn("owner_id = %s", cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_args.args[1], ("alice",))

    def handler(self, path="/api/uploads", data=b"Text", token=""):
        handler = HRHandler.__new__(HRHandler)
        handler.path = path
        handler.headers = {"Host": "localhost", "Cookie": f"pv_session={token}", "Content-Length": str(len(data)), "X-File-Name": "leave.txt"}
        handler.rfile = MagicMock(wraps=io.BytesIO(data))
        handler.send_json = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        return handler

    def test_anonymous_revoked_and_expired_sessions_cannot_read_or_upload(self):
        revoked = self.sessions.create("alice")
        self.sessions.revoke(revoked)
        expired = self.sessions.create("alice")
        self.sessions._sessions[expired] = ("alice", 0)
        with patch("backend.server.API_CONTROLLER", self.controller):
            for token in ("", "invalid", revoked, expired):
                for method in ("do_GET", "do_POST"):
                    with self.subTest(token=token, method=method):
                        handler = self.handler(token=token)
                        getattr(handler, method)()
                        self.assertEqual(handler.send_json.call_args.args[0], 401)
                        handler.rfile.read.assert_not_called()
        self.vectors.upsert.assert_not_called()

    def test_http_upload_decodes_filename_and_indexes(self):
        token = self.sessions.create("alice")
        handler = self.handler(data=b"Annual leave policy", token=token)
        handler.headers["X-File-Name"] = "annual%20leave.txt"
        with patch("backend.server.API_CONTROLLER", self.controller):
            handler.do_POST()
        self.assertEqual(handler.send_json.call_args.args[0], 201)
        self.assertEqual(handler.send_json.call_args.args[1]["document"]["title"], "annual leave.txt")

    def test_oversized_upload_is_rejected_before_reading_body(self):
        handler = self.handler(token=self.sessions.create("alice"))
        handler.headers["Content-Length"] = str(UploadService.MAX_BYTES + 1)
        with patch("backend.server.API_CONTROLLER", self.controller):
            handler.do_POST()
        self.assertEqual(handler.send_json.call_args.args[0], 413)
        handler.rfile.read.assert_not_called()

    def test_cross_origin_upload_is_rejected_before_reading(self):
        handler = self.handler(token=self.sessions.create("alice"))
        handler.headers["Origin"] = "https://other.example"
        with patch("backend.server.API_CONTROLLER", self.controller):
            handler.do_POST()
        self.assertEqual(handler.send_json.call_args.args[0], 403)
        handler.rfile.read.assert_not_called()

    def test_upload_page_redirects_anonymous_user_to_login(self):
        handler = self.handler(path="/upload")
        with patch("backend.server.API_CONTROLLER", self.controller):
            handler.do_GET()
        handler.send_response.assert_called_once_with(302)
        handler.send_header.assert_any_call("Location", "/login")


if __name__ == "__main__":
    unittest.main()
