import time
from dataclasses import asdict
from http import HTTPStatus

from backend.models import ApiResponse
from backend.repositories.document_repository import InMemoryDocumentRepository
from backend.services.audit_service import AuditService
from backend.services.rag_service import RagService
from backend.services.security_service import SecurityService
from backend.services.session_service import SessionService


class ApiController:
    """Coordinates HTTP use cases; it contains no HTTP-server implementation."""

    def __init__(
        self,
        users: dict[str, dict[str, str]],
        documents: InMemoryDocumentRepository,
        sessions: SessionService,
        rag: RagService,
        security: SecurityService,
        audit: AuditService,
    ) -> None:
        self.users, self.documents, self.sessions = users, documents, sessions
        self.rag, self.security, self.audit = rag, security, audit

    def user(self, token: str) -> dict | None:
        return self.sessions.user_for_token(token)

    def login(self, payload: dict) -> ApiResponse:
        user_id = str(payload.get("userId", ""))
        if user_id not in self.users: return ApiResponse(400, {"error": "Unknown demo identity."})
        token = self.sessions.create(user_id)
        return ApiResponse(200, {"session": token, "user": {"id": user_id, **self.users[user_id]}, "notice": "Demo-only identity switch. Production requires OIDC, MFA, and short-lived server-side sessions."})

    def ask(self, user: dict, payload: dict) -> ApiResponse:
        started, question = time.perf_counter(), str(payload.get("question", "")).strip()
        if not question: return ApiResponse(400, {"error": "A question is required."})
        controls = self.security.controls_for_query(question)
        if "prompt-injection-block" in controls:
            cid = self.audit.record(user["id"], "rag.query", "blocked", 0, started, controls)
            return ApiResponse(200, {"status": "blocked", "correlationId": cid, "answer": "Request blocked by the AI safety policy. No documents were retrieved.", "citations": [], "controls": controls})
        docs = self.rag.retrieve(user, question, self.documents.all()); controls.append("authorise-before-retrieve")
        cid = self.audit.record(user["id"], "rag.query", "grounded" if docs else "no_authorised_source", len(docs), started, controls)
        return ApiResponse(200, {"status": "grounded" if docs else "no_authorised_source", "correlationId": cid, "answer": self.rag.answer(question, docs), "citations": [{"id": doc["id"], "title": doc["title"], "classification": doc["classification"]} for doc in docs], "controls": controls, "pipeline": self.rag.pipeline_name})

    def audit_events(self, user: dict[str, str]) -> ApiResponse:
        if user["role"] not in {"hr_payroll", "hr_partner"}:
            return ApiResponse(403, {"error": "Audit-view privilege required."})
        return ApiResponse(200, {"events": [asdict(event) for event in self.audit.recent()], "policyVersion": "HR-RAG-ACCESS-2026.1"})

    def ingest(self, user: dict[str, str], payload: dict, started: float) -> ApiResponse:
        if user["role"] != "hr_payroll":
            cid = self.audit.record(user["id"], "document.ingest", "denied", 0, started, ["least-privilege"])
            return ApiResponse(403, {"error": "Only HR Payroll may ingest payroll documents.", "correlationId": cid})
        title, content, owner = (str(payload.get(key, "")).strip() for key in ("title", "content", "ownerId"))
        if not title or not content or owner not in self.users:
            return ApiResponse(400, {"error": "Title, content, and a valid owner are required."})
        document = self.documents.create_payslip(title, content, owner)
        cid = self.audit.record(user["id"], "document.ingest", "accepted", 1, started, ["hr-payroll-ingestion"])
        return ApiResponse(201, {"document": {key: document[key] for key in ("id", "title", "classification", "owner_id")}, "correlationId": cid, "notice": "Synthetic demo document accepted. Production ingestion must malware-scan, classify, encrypt, version, and index asynchronously."})
