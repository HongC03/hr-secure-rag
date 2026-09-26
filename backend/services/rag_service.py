import re
from typing import Any

from backend.repositories.pgvector_repository import PgVectorRepository
from backend.services.access_service import AccessService
from backend.services.chunking_service import DocumentChunkingService
from backend.services.embedding_service import EmbeddingGemmaEmbedding
from backend.services.llm_service import LlmService, LlmUnavailableError

class RagService:
    def __init__(self, access: AccessService, pgvector_repository: PgVectorRepository, llm: LlmService | None = None) -> None:
        if pgvector_repository is None:
            raise ValueError("A pgvector repository is required")
        self.access, self.pgvector_repository = access, pgvector_repository
        self.llm = llm
        self.chunking = DocumentChunkingService()
        self.embedding_model = EmbeddingGemmaEmbedding()

    @property
    def pipeline_name(self) -> str:
        return "PostgreSQL pgvector + RLS → authorised context → LLM"

    def index_document(self, document: dict[str, Any]) -> None:
        """Persist a new synthetic document before publishing it to the source corpus."""
        self.pgvector_repository.upsert(self.chunking.chunk_document(document), self.embedding_model)

    def retrieve(self, user: dict[str, str], question: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        permitted_sources = self.access.allowed_documents(user, documents)
        # Both the app allowlist and PostgreSQL RLS filter rows before ranking.
        allowed_sources = {document["id"]: document for document in permitted_sources}
        if not allowed_sources:
            return []
        rows = self.pgvector_repository.search(
            user, self.embedding_model.get_query_embedding(question), sorted(allowed_sources)
        )

        def allowed_row(row: dict[str, Any]) -> bool:
            source = allowed_sources.get(row["parent_document_id"])
            return bool(
                source
                and all(row[key] == source[key] for key in ("document_type", "classification", "owner_id"))
                and self.access.can_read(user, row)
            )

        terms = set(re.findall(r"[a-z]{2,}", question.lower()))
        ranked = []
        for row in rows:
            corpus = set(re.findall(r"[a-z]{2,}", f"{row['title']} {row['content']} {' '.join(row['tags'])}".lower()))
            if score := len(terms & corpus):
                if allowed_row(row):
                    ranked.append((score, row))
        hits = [row for _, row in sorted(ranked, reverse=True, key=lambda item: item[0])]
        return [row for row in self.pgvector_repository.include_neighbours(user, hits) if allowed_row(row)]

    def answer(self, question: str, documents: list[dict[str, Any]]) -> str:
        if not documents: return "I cannot find an authorised source for that request. I will not search or infer from documents outside your approved scope."
        if self.llm is None:
            raise LlmUnavailableError("No answer provider is configured")
        context = "\n\n".join(
            f"[{doc['id']}] {doc['title']}\n{doc['content']}" for doc in documents
        )
        return self.llm.answer(question, context)
