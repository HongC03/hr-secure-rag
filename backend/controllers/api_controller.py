import time
import re
from dataclasses import asdict
from http import HTTPStatus

from backend import api_error_message, api_text
from backend.models import ApiResponse
from backend.repositories.document_repository import InMemoryDocumentRepository
from backend.services.audit_service import AuditService
from backend.services.llm_service import LlmUnavailableError
from backend.services.rag_service import RagService
from backend.services.security_service import SecurityService
from backend.services.session_service import SessionService
from backend.repositories.user_repository import UserRepository


class ApiController:
    """Coordinates HTTP use cases; it contains no HTTP-server implementation."""

    def __init__(
        self,
        users: UserRepository | None,
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
        user_id, password = payload.get("userId"), payload.get("password")
        if not isinstance(user_id, str) or not isinstance(password, str) or not user_id or not password or len(user_id) > 128 or len(password) > 1024:
            return ApiResponse(400, {"error": api_error_message.LOGIN_CREDENTIALS_REQUIRED})
        if self.users is None:
            return ApiResponse(503, {"error": api_error_message.ACCOUNT_DATABASE_NOT_CONFIGURED})
        try:
            user = self.users.authenticate(user_id, password)
        except self.users.psycopg.Error:
            return ApiResponse(503, {"error": api_error_message.ACCOUNT_DATABASE_UNAVAILABLE})
        if user is None:
            return ApiResponse(401, {"error": api_error_message.INVALID_CREDENTIALS})
        try:
            token = self.sessions.create(user_id)
        except self.users.psycopg.Error:
            return ApiResponse(503, {"error": api_error_message.ACCOUNT_DATABASE_UNAVAILABLE})
        if token is None:
            return ApiResponse(401, {"error": api_error_message.INVALID_CREDENTIALS})
        return ApiResponse(200, {"session": token, "user": user})

    def register(self, payload: dict) -> ApiResponse:
        username, name, password = payload.get("username"), payload.get("name"), payload.get("password")
        if not isinstance(username, str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{2,31}", username):
            return ApiResponse(400, {"error": api_error_message.USERNAME_INVALID})
        if not isinstance(name, str):
            return ApiResponse(400, {"error": api_error_message.FULL_NAME_REQUIRED})
        name = " ".join(name.split())
        if not 2 <= len(name) <= 120 or any(ord(char) < 32 or ord(char) == 127 for char in name):
            return ApiResponse(400, {"error": api_error_message.FULL_NAME_INVALID})
        if not isinstance(password, str) or not 8 <= len(password) <= 1024:
            return ApiResponse(400, {"error": api_error_message.PASSWORD_INVALID})
        if self.users is None:
            return ApiResponse(503, {"error": api_error_message.ACCOUNT_DATABASE_NOT_CONFIGURED})
        try:
            user = self.users.register(username.lower(), name, password)
            token = self.sessions.create(user["id"])
        except self.users.psycopg.errors.UniqueViolation:
            return ApiResponse(409, {"error": api_error_message.USERNAME_TAKEN})
        except self.users.psycopg.Error:
            return ApiResponse(503, {"error": api_error_message.ACCOUNT_DATABASE_UNAVAILABLE})
        if token is None:
            return ApiResponse(503, {"error": api_error_message.SESSION_START_FAILED})
        return ApiResponse(201, {"session": token, "user": user})

    def ask(self, user: dict, payload: dict) -> ApiResponse:
        started = time.perf_counter()
        question = self.security.normalise_query(payload.get("question"))
        if question is None:
            return ApiResponse(400, {"error": api_error_message.QUESTION_INVALID})
        controls = self.security.controls_for_query()
        docs = self.rag.retrieve(user, question, self.documents.all()); controls.append("authorise-before-retrieve")
        try:
            answer = self.rag.answer(question, docs)
        except LlmUnavailableError:
            cid = self.audit.record(user["id"], "rag.query", "answer_unavailable", len(docs), started, controls)
            return ApiResponse(503, {"error": api_error_message.ANSWER_SERVICE_UNAVAILABLE, "correlationId": cid})
        cid = self.audit.record(user["id"], "rag.query", "grounded" if docs else "no_authorised_source", len(docs), started, controls)
        return ApiResponse(200, {"status": "grounded" if docs else "no_authorised_source", "correlationId": cid, "answer": answer, "citations": [{"id": doc["id"], "title": doc["title"], "classification": doc["classification"]} for doc in docs], "controls": controls, "pipeline": self.rag.pipeline_name})

    def audit_events(self, user: dict[str, str]) -> ApiResponse:
        if user["role"] not in {"hr_payroll", "hr_partner"}:
            return ApiResponse(403, {"error": api_error_message.AUDIT_PRIVILEGE_REQUIRED})
        return ApiResponse(200, {"events": [asdict(event) for event in self.audit.recent()], "policyVersion": api_text.POLICY_VERSION})

    def ingest(self, user: dict[str, str], payload: dict, started: float) -> ApiResponse:
        if user["role"] != "hr_payroll":
            cid = self.audit.record(user["id"], "document.ingest", "denied", 0, started, ["least-privilege"])
            return ApiResponse(403, {"error": api_error_message.PAYROLL_INGEST_FORBIDDEN, "correlationId": cid})
        title, content, owner = (str(payload.get(key, "")).strip() for key in ("title", "content", "ownerId"))
        if not title or not content or self.users is None:
            return ApiResponse(400, {"error": api_error_message.DOCUMENT_FIELDS_REQUIRED})
        try:
            owner_user = self.users.get(owner)
        except self.users.psycopg.Error:
            return ApiResponse(503, {"error": api_error_message.ACCOUNT_DATABASE_UNAVAILABLE})
        if owner_user is None:
            return ApiResponse(400, {"error": api_error_message.DOCUMENT_FIELDS_REQUIRED})
        document = self.documents.build_payslip(title, content, owner)
        try:
            self.rag.index_document(document)
        except Exception:
            cid = self.audit.record(user["id"], "document.ingest", "index_failed", 0, started, ["hr-payroll-ingestion"])
            return ApiResponse(503, {"error": api_error_message.DOCUMENT_INDEX_FAILED, "correlationId": cid})
        self.documents.add(document)
        cid = self.audit.record(user["id"], "document.ingest", "accepted", 1, started, ["hr-payroll-ingestion"])
        return ApiResponse(201, {"document": {key: document[key] for key in ("id", "title", "classification", "owner_id")}, "correlationId": cid, "notice": api_text.DOCUMENT_INGEST_NOTICE})
