"""PostgreSQL account lookup. Public user values never include password hashes."""
from __future__ import annotations

import secrets

from backend.repositories.pgvector_repository import PgVectorRepository
from backend.services.password_service import hash_password, verify_password


class UserRepository:
    def __init__(self, database_url: str) -> None:
        import psycopg

        self.database_url = database_url
        self.psycopg = psycopg
        # Keep unknown-account checks close in cost to a wrong password check.
        self._dummy_hash = hash_password("unknown-account-dummy")

    @classmethod
    def from_environment(cls) -> "UserRepository | None":
        database = PgVectorRepository.from_environment()
        return cls(database.database_url) if database else None

    def get(self, user_id: str) -> dict[str, str] | None:
        with self.psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, name, role, department, label, login_name FROM app_users WHERE user_id = %s AND active",
                (user_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return dict(zip(("id", "name", "role", "department", "label", "loginName"), row, strict=True))

    def authenticate(self, user_id: str, password: str) -> dict[str, str] | None:
        with self.psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, name, role, department, label, login_name, password_hash FROM app_users WHERE (user_id = %s OR login_name = %s) AND active",
                (user_id, user_id),
            )
            row = cursor.fetchone()
        stored = row[6] if row else self._dummy_hash
        if not verify_password(password, stored) or row is None:
            return None
        return dict(zip(("id", "name", "role", "department", "label", "loginName"), row[:6], strict=True))

    def register(self, username: str, name: str, password: str) -> dict[str, str]:
        user_id = f"self_{secrets.token_hex(16)}"
        login_name = f"@{username}"
        with self.psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO app_users (user_id, login_name, name, department, label, password_hash)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING user_id, name, role, department, label, login_name""",
                (user_id, login_name, name, "Unverified", "Self-registered employee", hash_password(password)),
            )
            row = cursor.fetchone()
        return dict(zip(("id", "name", "role", "department", "label", "loginName"), row, strict=True))
