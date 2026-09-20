from dataclasses import dataclass
from typing import Any
from datetime import UTC, datetime
import time
import uuid


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: dict[str, Any]


@dataclass(frozen=True)
class AuditEvent:
    """A redacted event suitable for the demo audit stream."""

    timestamp: str
    correlation_id: str
    actor: str
    action: str
    outcome: str
    returned_document_count: int
    latency_ms: int
    controls: list[str]


def new_audit_event(
    actor: str,
    action: str,
    outcome: str,
    documents: int,
    started: float,
    controls: list[str],
) -> AuditEvent:
    """Build an audit event without retaining a raw query or document content."""
    return AuditEvent(
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        correlation_id=str(uuid.uuid4()),
        actor=actor,
        action=action,
        outcome=outcome,
        returned_document_count=documents,
        latency_ms=round((time.perf_counter() - started) * 1000),
        controls=list(controls),
    )
