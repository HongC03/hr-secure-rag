import secrets
import time
from threading import Lock


class SessionService:
    """Expiring server-side sessions. The cookie contains only an opaque token."""

    def __init__(self, users, lifetime_seconds: int = 8 * 60 * 60) -> None:
        self._users = users
        self._sessions: dict[str, tuple[str, float]] = {}
        self._lifetime = lifetime_seconds
        self._lock = Lock()

    def _user(self, user_id: str) -> dict[str, str] | None:
        if self._users is None:
            return None
        if hasattr(self._users, "get") and not isinstance(self._users, dict):
            return self._users.get(user_id)
        data = self._users.get(user_id)
        return {"id": user_id, **data} if data else None

    def create(self, user_id: str) -> str | None:
        if not self._user(user_id):
            return None
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = (user_id, time.monotonic() + self._lifetime)
        return token

    def user_for_token(self, token: str) -> dict[str, str] | None:
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            if not session:
                return None
            user_id, expires_at = session
            if time.monotonic() >= expires_at:
                del self._sessions[token]
                return None
        user = self._user(user_id)
        if user is None:
            self.revoke(token)
        return user

    def revoke(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)
