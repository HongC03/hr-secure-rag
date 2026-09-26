"""PostgreSQL account lookup. Public user values never include password hashes."""
from __future__ import annotations

import secrets

from backend.repositories.pgvector_repository import PgVectorRepository
from backend.services.password_service import hash_password, verify_password


class UserRepository:
    def __init__(self, database_url: str, pool=None) -> None:
        import psycopg
        from psycopg_pool import ConnectionPool

        self.database_url = database_url
        self.psycopg = psycopg
        self._owns_pool = pool is None
        self.pool = pool if pool is not None else ConnectionPool(
            database_url, min_size=1, max_size=10, kwargs={"connect_timeout": 5}, open=True
        )
        # Keep unknown-account checks close in cost to a wrong password check.
        self._dummy_hash = hash_password("unknown-account-dummy")

    @classmethod
    def from_environment(cls, pool=None) -> "UserRepository":
        return cls(PgVectorRepository.database_url_from_environment(), pool=pool)

    def close(self) -> None:
        if self._owns_pool:
            self.pool.close()

    def get(self, user_id: str) -> dict[str, str] | None:
        with self.pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, name, role, department, label, login_name FROM app_users WHERE user_id = %s AND active",
                (user_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return dict(zip(("id", "name", "role", "department", "label", "loginName"), row, strict=True))

    def authenticate(self, user_id: str, password: str) -> dict[str, str] | None:
        login_name = user_id.lower() if user_id.startswith("@") else f"@{user_id.lower()}"
        with self.pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT user_id, name, role, department, label, login_name, password_hash
                   FROM app_users WHERE (user_id = %s OR login_name = %s) AND active
                   ORDER BY (user_id = %s) DESC""",
                (user_id, login_name, user_id),
            )
            rows = cursor.fetchall()
        matched = None
        for row in rows:
            if verify_password(password, row[6]) and matched is None:
                matched = row
        if not rows:
            verify_password(password, self._dummy_hash)
        if matched is None:
            return None
        return dict(zip(("id", "name", "role", "department", "label", "loginName"), matched[:6], strict=True))

    def register(self, username: str, name: str, password: str) -> dict[str, str]:
        user_id = f"self_{secrets.token_hex(16)}"
        login_name = f"@{username}"
        with self.pool.connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO app_users (user_id, login_name, name, department, label, password_hash)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING user_id, name, role, department, label, login_name""",
                (user_id, login_name, name, "Unverified", "Self-registered employee", hash_password(password)),
            )
            row = cursor.fetchone()
        return dict(zip(("id", "name", "role", "department", "label", "loginName"), row, strict=True))
