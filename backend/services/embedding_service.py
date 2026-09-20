"""Local EmbeddingGemma adapter shared by LlamaIndex and pgvector."""

from typing import Any

from llama_index.core.embeddings import BaseEmbedding
from pydantic import PrivateAttr


MODEL_ID = "google/embeddinggemma-300M"
EMBEDDING_DIMENSIONS = 768


def document_embedding_text(title: str, content: str) -> str:
    """Format a document exactly as EmbeddingGemma's document example expects."""
    return f"title: {title} | text: {content}"


class EmbeddingGemmaEmbedding(BaseEmbedding):
    """LlamaIndex-compatible, on-device Google EmbeddingGemma embedding model."""

    model_name: str = MODEL_ID
    _model: Any = PrivateAttr(default=None)

    @property
    def model(self) -> Any:
        """Load the model only when an embedding is first requested."""
        if self._model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            device = "mps" if torch.backends.mps.is_available() else "cpu"
            self._model = SentenceTransformer(self.model_name, device=device)
        return self._model

    @staticmethod
    def _as_embedding(vector: Any) -> list[float]:
        embedding = [float(value) for value in vector]
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"EmbeddingGemma returned {len(embedding)} dimensions; "
                f"expected {EMBEDDING_DIMENSIONS}."
            )
        return embedding

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._as_embedding(
            self.model.encode(
                query,
                prompt_name="Retrieval-query",
                normalize_embeddings=True,
            )
        )

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._as_embedding(self.model.encode(text, normalize_embeddings=True))

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [self._as_embedding(vector) for vector in vectors]
