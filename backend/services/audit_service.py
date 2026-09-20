from collections import deque

from backend.models import AuditEvent, new_audit_event


class AuditService:
    """Stores redacted, bounded demo audit metadata.

    Production must deliver these events to immutable external storage rather
    than retaining them in process memory.
    """

    def __init__(self, max_events: int = 200) -> None:
        self._events: deque[AuditEvent] = deque(maxlen=max_events)

    def record(
        self,
        actor: str,
        action: str,
        outcome: str,
        documents: int,
        started: float,
        controls: list[str],
    ) -> str:
        event = new_audit_event(actor, action, outcome, documents, started, controls)
        self._events.append(event)
        return event.correlation_id

    def recent(self, limit: int = 12) -> list[AuditEvent]:
        return list(self._events)[-limit:]
