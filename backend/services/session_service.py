import secrets


class SessionService:
    """Demo-only server-side sessions for the synthetic identity selector."""

    def __init__(self, users: dict[str, dict[str, str]]) -> None:
        self._users = users
        self._sessions: dict[str, str] = {}

    def create(self, user_id: str) -> str | None:
        if user_id not in self._users:
            return None
        token = secrets.token_urlsafe(24)
        self._sessions[token] = user_id
        return token

    def user_for_token(self, token: str) -> dict[str, str] | None:
        user_id = self._sessions.get(token)
        if user_id not in self._users:
            return None
        return {"id": user_id, **self._users[user_id]}
