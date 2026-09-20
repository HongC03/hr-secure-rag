"""Document-aware chunking and context reconstruction for secure RAG."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


class DocumentChunkingService:
    """Creates retrievable chunks without splitting atomic HR records.

    Payroll and tax records are kept whole: their labels, values, and privacy
    context must stay together. Long policy/runbook documents are split with
    overlap so a retrieval hit can safely bring adjacent context to the answer.
    """

    ATOMIC_DOCUMENT_TYPES = frozenset({"payslip", "tax_statement"})
    MAX_WORDS = 120
    OVERLAP_WORDS = 30

    def chunk_documents(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [chunk for document in documents for chunk in self.chunk_document(document)]

    def chunk_document(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        source_id, content = document["id"], document["content"]
        parts = [content] if document["document_type"] in self.ATOMIC_DOCUMENT_TYPES else self._split(content)
        return [
            {
                **deepcopy(document),
                "id": source_id if len(parts) == 1 else f"{source_id}::chunk::{index + 1}",
                "parent_document_id": source_id,
                "chunk_index": index,
                "chunk_count": len(parts),
                "content": part,
            }
            for index, part in enumerate(parts)
        ]

    def include_neighbours(
        self, retrieved: list[dict[str, Any]], authorised_chunks: list[dict[str, Any]], window: int = 1
    ) -> list[dict[str, Any]]:
        """Return each hit plus nearby chunks from the already-authorised corpus."""
        wanted = {
            (chunk["parent_document_id"], index)
            for chunk in retrieved
            for index in range(max(0, chunk["chunk_index"] - window), chunk["chunk_index"] + window + 1)
        }
        neighbours = [
            chunk for chunk in authorised_chunks if (chunk["parent_document_id"], chunk["chunk_index"]) in wanted
        ]
        # Keep each local context in source order; retain which chunk caused it.
        hit_keys = {chunk["id"] for chunk in retrieved}
        return [
            {**chunk, "retrieval_hit": chunk["id"] in hit_keys}
            for chunk in sorted(neighbours, key=lambda chunk: (chunk["parent_document_id"], chunk["chunk_index"]))
        ]

    def _split(self, content: str) -> list[str]:
        words = content.split()
        if len(words) <= self.MAX_WORDS:
            return [content]
        step = self.MAX_WORDS - self.OVERLAP_WORDS
        return [" ".join(words[start : start + self.MAX_WORDS]) for start in range(0, len(words), step)]
