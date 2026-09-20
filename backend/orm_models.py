"""Optional SQLAlchemy mappings for the PostgreSQL/pgvector persistence schema.

The SQL migration remains the source of truth for extensions, indexes, grants,
and row-level-security policies.  The live repository intentionally continues
to use explicit SQL because it must set PostgreSQL's transaction-local RLS
context before each query.
"""
from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base for optional ORM use; it does not create or migrate the schema."""


class HrDocumentChunk(Base):
    """Human-readable ORM mapping of ``hr_document_chunks``.

    Access must still be mediated through :class:`PgVectorRepository` so the
    database RLS identity and the application policy are both enforced.
    """

    __tablename__ = "hr_document_chunks"

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    parent_document_id: Mapped[str] = mapped_column(String, nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False, server_default="0")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    classification: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
