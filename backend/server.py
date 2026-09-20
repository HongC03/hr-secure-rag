#!/usr/bin/env python3
"""Secure HR-document RAG demo. Uses synthetic data; it is not a production payroll system."""
from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from backend.controllers.api_controller import ApiController
from backend.repositories.document_repository import InMemoryDocumentRepository
from backend.services.access_service import AccessService
from backend.services.audit_service import AuditService
from backend.services.rag_service import RagService
from backend.services.security_service import SecurityService
from backend.services.session_service import SessionService
from backend.repositories.pgvector_repository import PgVectorRepository
from seed import demo_data

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend" / "dist"
POLICY_VERSION = "HR-RAG-ACCESS-2026.1"
ACCESS_SERVICE = AccessService()
PGVECTOR_REPOSITORY = PgVectorRepository.from_environment()
RAG_SERVICE = RagService(ACCESS_SERVICE, PGVECTOR_REPOSITORY)
SECURITY_SERVICE = SecurityService()
DOCUMENT_REPOSITORY = InMemoryDocumentRepository(demo_data.DOCUMENTS)
SESSION_SERVICE = SessionService(demo_data.USERS)
AUDIT_SERVICE = AuditService()
# Compatibility aliases for existing policy tests and interactive demos.
SESSIONS = SESSION_SERVICE
AUDIT = AUDIT_SERVICE

def utc_now() -> str: return datetime.now(UTC).isoformat(timespec="seconds")

def record_audit(actor: str, action: str, outcome: str, documents: int, started: float, controls: list[str]) -> str:
    """Compatibility adapter; application use cases call AuditService directly."""
    return AUDIT_SERVICE.record(actor, action, outcome, documents, started, controls)

API_CONTROLLER = ApiController(demo_data.USERS, DOCUMENT_REPOSITORY, SESSION_SERVICE, RAG_SERVICE, SECURITY_SERVICE, AUDIT_SERVICE)

def can_read(user: dict[str, str], doc: dict[str, Any]) -> bool:
    return ACCESS_SERVICE.can_read(user, doc)

def allowed_documents(user: dict[str, str]) -> list[dict[str, Any]]:
    return ACCESS_SERVICE.allowed_documents(user, DOCUMENT_REPOSITORY.all())

def retrieve_authorised(user: dict[str, str], question: str) -> list[dict[str, Any]]:
    """Search only the caller's permitted corpus—important to prevent RAG data leakage."""
    return RAG_SERVICE.retrieve(user, question, DOCUMENT_REPOSITORY.all())

def llamaindex_authorised_retrieval(user: dict[str, str], question: str) -> list[dict[str, Any]]:
    """Compatibility name for the in-memory LlamaIndex retrieval path."""
    return RAG_SERVICE.retrieve(user, question, DOCUMENT_REPOSITORY.all())

def langchain_answer(question: str, docs: list[dict[str, Any]]) -> str:
    """Compatibility name for the LangChain answer-composition path."""
    return RAG_SERVICE.answer(question, docs)

class HRHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def send_json(self, status: int, data: dict[str, Any]) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def body(self) -> dict[str, Any]:
        size = int(self.headers.get("Content-Length", "0")); return json.loads(self.rfile.read(size) or b"{}")

    def current_user(self) -> dict[str, str] | None:
        return API_CONTROLLER.user(self.headers.get("X-Demo-Session", ""))

    def require_user(self) -> dict[str, str] | None:
        user = self.current_user()
        if not user: self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "Sign in is required."})
        return user

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health": return self.send_json(200, {"status": "ok", "policyVersion": POLICY_VERSION})
        if self.path == "/api/me":
            user = self.current_user(); return self.send_json(200, {"user": user, "policyVersion": POLICY_VERSION} if user else {"user": None, "policyVersion": POLICY_VERSION})
        if self.path == "/api/audit":
            user = self.require_user()
            if not user: return
            response = API_CONTROLLER.audit_events(user)
            return self.send_json(response.status, response.body)
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        started = time.perf_counter()
        try: payload = self.body()
        except json.JSONDecodeError: return self.send_json(400, {"error": "Invalid JSON."})
        if self.path == "/api/login":
            response = API_CONTROLLER.login(payload)
            return self.send_json(response.status, response.body)
        user = self.require_user()
        if not user: return
        if self.path == "/api/ask":
            response = API_CONTROLLER.ask(user, payload)
            return self.send_json(response.status, response.body)
        if self.path == "/api/documents":
            response = API_CONTROLLER.ingest(user, payload, started)
            return self.send_json(response.status, response.body)
        return self.send_json(404, {"error": "Unknown endpoint."})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{utc_now()}] {fmt % args}")

if __name__ == "__main__":
    if not FRONTEND_DIR.exists():
        raise SystemExit("React build is missing. Run: cd frontend && npm run build")
    server = ThreadingHTTPServer(("127.0.0.1", 8001), HRHandler)
    print("Secure HR RAG demo: http://127.0.0.1:8001")
    server.serve_forever()
