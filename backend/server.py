#!/usr/bin/env python3
"""Secure HR-document RAG demo. Uses synthetic data; it is not a production payroll system."""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from backend import api_error_message
from backend.api_text import POLICY_VERSION
from backend.controllers.api_controller import ApiController
from backend.repositories.document_repository import InMemoryDocumentRepository
from backend.services.access_service import AccessService
from backend.services.audit_service import AuditService
from backend.services.rag_service import RagService
from backend.services.llm_factory import llm_from_environment
from backend.services.security_service import SecurityService
from backend.services.session_service import SessionService
from backend.repositories.pgvector_repository import PgVectorRepository
from backend.repositories.user_repository import UserRepository
from seed import demo_data
from seed.fixture_data import load_test_documents

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend" / "dist"
LOGGER = logging.getLogger("peoplevault.server")


def configure_server_logging() -> None:
    """Write UTC server logs to standard output for local runs and Docker."""
    if LOGGER.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)sZ %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    LOGGER.setLevel(level if level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"} else "INFO")
    LOGGER.propagate = False


ACCESS_SERVICE = AccessService()
PGVECTOR_REPOSITORY = PgVectorRepository.from_environment()
RAG_SERVICE = RagService(ACCESS_SERVICE, PGVECTOR_REPOSITORY, llm_from_environment())
SECURITY_SERVICE = SecurityService()
if os.environ.get("LOAD_TEST_DATA") == "1":
    # Keep source IDs aligned with rows seeded into pgvector. Fixture versions
    # replace matching demo documents, such as Alice's sample payslip.
    source_documents = {document["id"]: document for document in demo_data.DOCUMENTS}
    source_documents.update({document["id"]: document for document in load_test_documents()})
    DOCUMENT_REPOSITORY = InMemoryDocumentRepository(list(source_documents.values()))
else:
    DOCUMENT_REPOSITORY = InMemoryDocumentRepository(demo_data.DOCUMENTS)
USER_REPOSITORY = UserRepository.from_environment()
SESSION_SERVICE = SessionService(USER_REPOSITORY)
AUDIT_SERVICE = AuditService()
# Compatibility aliases for existing policy tests and interactive demos.
SESSIONS = SESSION_SERVICE
AUDIT = AUDIT_SERVICE

def utc_now() -> str: return datetime.now(UTC).isoformat(timespec="seconds")

def record_audit(actor: str, action: str, outcome: str, documents: int, started: float, controls: list[str]) -> str:
    """Compatibility adapter; application use cases call AuditService directly."""
    return AUDIT_SERVICE.record(actor, action, outcome, documents, started, controls)

API_CONTROLLER = ApiController(USER_REPOSITORY, DOCUMENT_REPOSITORY, SESSION_SERVICE, RAG_SERVICE, SECURITY_SERVICE, AUDIT_SERVICE)

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

class HRHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def handle_one_request(self) -> None:
        self.request_started = time.perf_counter()
        super().handle_one_request()

    def send_json(self, status: int, data: dict[str, Any], cookie: str | None = None) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store")
        if cookie is not None: self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def body(self) -> dict[str, Any]:
        size = int(self.headers.get("Content-Length", "0"))
        if size < 0 or size > 16384: raise ValueError(api_error_message.REQUEST_TOO_LARGE)
        payload = json.loads(self.rfile.read(size) or b"{}")
        if not isinstance(payload, dict): raise ValueError(api_error_message.JSON_OBJECT_REQUIRED)
        return payload

    def session_token(self) -> str:
        cookie = SimpleCookie()
        try: cookie.load(self.headers.get("Cookie", ""))
        except Exception: return ""
        return cookie["pv_session"].value if "pv_session" in cookie else ""

    def session_cookie(self, token: str = "", clear: bool = False) -> str:
        secure = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""
        age = 0 if clear else 8 * 60 * 60
        return f"pv_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={age}{secure}"

    def current_user(self) -> dict[str, str] | None:
        try: return API_CONTROLLER.user(self.session_token())
        except Exception: return None

    def require_user(self) -> dict[str, str] | None:
        user = self.current_user()
        if not user: self.send_json(HTTPStatus.UNAUTHORIZED, {"error": api_error_message.SIGN_IN_REQUIRED})
        return user

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/login":
            self.path = "/index.html"
            return super().do_GET()
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
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            return self.send_json(403, {"error": api_error_message.INVALID_REQUEST_ORIGIN})
        try: payload = self.body()
        except (json.JSONDecodeError, ValueError): return self.send_json(400, {"error": api_error_message.INVALID_JSON_REQUEST})
        if self.path in {"/api/login", "/api/register"}:
            response = API_CONTROLLER.login(payload) if self.path == "/api/login" else API_CONTROLLER.register(payload)
            if response.status in {200, 201}:
                token = response.body["session"]
                SESSION_SERVICE.revoke(self.session_token())
                return self.send_json(response.status, {"user": response.body["user"]}, self.session_cookie(token))
            return self.send_json(response.status, response.body)
        if self.path == "/api/logout":
            SESSION_SERVICE.revoke(self.session_token())
            return self.send_json(200, {"user": None}, self.session_cookie(clear=True))
        user = self.require_user()
        if not user: return
        if self.path == "/api/ask":
            response = API_CONTROLLER.ask(user, payload)
            return self.send_json(response.status, response.body)
        if self.path == "/api/documents":
            response = API_CONTROLLER.ingest(user, payload, started)
            return self.send_json(response.status, response.body)
        return self.send_json(404, {"error": api_error_message.UNKNOWN_ENDPOINT})

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        path = getattr(self, "path", "").partition("?")[0]
        duration_ms = round((time.perf_counter() - self.request_started) * 1000)
        level = logging.ERROR if isinstance(code, int) and code >= 500 else logging.INFO
        LOGGER.log(level, "request method=%r path=%r status=%s duration_ms=%s", getattr(self, "command", "-"), path, code, duration_ms)

    def log_message(self, fmt: str, *args: Any) -> None:
        # The default handler prints the raw request line, including query strings.
        LOGGER.warning("request_error method=%r path=%r", getattr(self, "command", "-"), getattr(self, "path", "").partition("?")[0])


class LoggingHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request: Any, client_address: Any) -> None:
        error_type = sys.exc_info()[0]
        LOGGER.error("unhandled_request_error type=%s", error_type.__name__ if error_type else "unknown")


if __name__ == "__main__":
    configure_server_logging()
    if not FRONTEND_DIR.exists():
        raise SystemExit("React build is missing. Run: cd frontend && npm run build")
    server = LoggingHTTPServer(("127.0.0.1", 8001), HRHandler)
    LOGGER.info("server_started address=http://127.0.0.1:8001")
    server.serve_forever()
