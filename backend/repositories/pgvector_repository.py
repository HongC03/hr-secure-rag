"""PostgreSQL + pgvector adapter. Enabled only when PGVECTOR_DATABASE_URL is set."""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

from backend.services.embedding_service import document_embedding_text


def _load_local_dotenv() -> None:
    """Load the project's ignored local `.env` without overriding deployed settings."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    load_dotenv(os.path.join(project_root, ".env"), override=False)


class PgVectorRepository:
    def __init__(self, database_url: str) -> None:
        try:
            import psycopg  # type: ignore
        except ImportError as error:
            raise RuntimeError("Install pgvector dependencies: pip install -r requirements-pgvector.txt") from error
        self.psycopg = psycopg
        self.database_url = database_url

    @classmethod
    def from_environment(cls) -> "PgVectorRepository | None":
        _load_local_dotenv()
        url = os.environ.get("PGVECTOR_DATABASE_URL")
        if not url:
            password = os.environ.get("POSTGRES_APP_PASSWORD")
            if password:
                user = os.environ.get("POSTGRES_APP_USER", "peoplevault_app")
                host = os.environ.get("PGVECTOR_DATABASE_HOST", "127.0.0.1")
                port = os.environ.get("PGVECTOR_DATABASE_PORT", "5432")
                database = os.environ.get("POSTGRES_DB", "peoplevault")
                url = (
                    f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}"
                    f"@{host}:{port}/{quote(database, safe='')}"
                )
        return cls(url) if url else None

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"

    @staticmethod
    def _set_security_context(cursor: Any, user: dict[str, str]) -> None:
        # Transaction-local settings are consumed by the database RLS policy.
        cursor.execute("SELECT set_config('app.user_id', %s, true)", (user["id"],))
        cursor.execute("SELECT set_config('app.user_role', %s, true)", (user["role"],))

    def search(
        self,
        user: dict[str, str],
        query_embedding: list[float],
        allowed_document_ids: list[str],
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Apply the app allowlist and RLS before cosine-distance ranking."""
        if not allowed_document_ids:
            return []
        sql = """
            SELECT document_id, parent_document_id, chunk_index, title, document_type, classification, owner_id, content, tags
            FROM hr_document_chunks
            WHERE parent_document_id = ANY(%s::text[])
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        with self.psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            self._set_security_context(cursor, user)
            cursor.execute(sql, (allowed_document_ids, self._vector_literal(query_embedding), limit))
            rows = cursor.fetchall()
        fields = ("id", "parent_document_id", "chunk_index", "title", "document_type", "classification", "owner_id", "content", "tags")
        return [dict(zip(fields, row, strict=True)) for row in rows]

    def include_neighbours(self, user: dict[str, str], hits: list[dict[str, Any]], window: int = 1) -> list[dict[str, Any]]:
        """Fetch local context after a hit; RLS applies to every neighbour query."""
        if not hits:
            return []
        sql = """
            SELECT document_id, parent_document_id, chunk_index, title, document_type, classification, owner_id, content, tags
            FROM hr_document_chunks
            WHERE parent_document_id = %s AND chunk_index BETWEEN %s AND %s
            ORDER BY chunk_index
        """
        fields = ("id", "parent_document_id", "chunk_index", "title", "document_type", "classification", "owner_id", "content", "tags")
        found: dict[str, dict[str, Any]] = {}
        with self.psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            self._set_security_context(cursor, user)
            for hit in hits:
                cursor.execute(sql, (hit["parent_document_id"], max(0, hit["chunk_index"] - window), hit["chunk_index"] + window))
                for row in cursor.fetchall():
                    chunk = dict(zip(fields, row, strict=True))
                    found[chunk["id"]] = chunk
        hit_ids = {hit["id"] for hit in hits}
        return [
            {**chunk, "retrieval_hit": chunk["id"] in hit_ids}
            for chunk in sorted(found.values(), key=lambda chunk: (chunk["parent_document_id"], chunk["chunk_index"]))
        ]

    def upsert(self, documents: list[dict[str, Any]], embedding_model: Any) -> None:
        sql = """
            INSERT INTO hr_document_chunks (document_id, parent_document_id, chunk_index, title, document_type, classification, owner_id, content, tags, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
            ON CONFLICT (document_id) DO UPDATE SET
              parent_document_id = EXCLUDED.parent_document_id, chunk_index = EXCLUDED.chunk_index,
              title = EXCLUDED.title, document_type = EXCLUDED.document_type,
              classification = EXCLUDED.classification, owner_id = EXCLUDED.owner_id,
              content = EXCLUDED.content, tags = EXCLUDED.tags, embedding = EXCLUDED.embedding
        """
        # Index jobs run as a dedicated HR Payroll service principal; RLS checks it.
        service_identity = {"id": "indexer", "role": "hr_payroll"}
        with self.psycopg.connect(self.database_url) as connection, connection.cursor() as cursor:
            self._set_security_context(cursor, service_identity)
            for document in documents:
                vector = embedding_model.get_text_embedding(
                    document_embedding_text(document["title"], document["content"])
                )
                cursor.execute(sql, (document["id"], document["parent_document_id"], document["chunk_index"], document["title"], document["document_type"], document["classification"], document["owner_id"], document["content"], document["tags"], self._vector_literal(vector)))
