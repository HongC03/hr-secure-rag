"""Embed and upsert the synthetic Markdown fixtures into local pgvector."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.repositories.pgvector_repository import PgVectorRepository
from backend.services.chunking_service import DocumentChunkingService
from backend.services.embedding_service import EmbeddingGemmaEmbedding
from seed.fixture_data import load_test_documents


def main() -> None:
    repository = PgVectorRepository.from_environment()
    if repository is None:
        raise SystemExit("Set POSTGRES_APP_PASSWORD in .env or set PGVECTOR_DATABASE_URL.")
    documents = load_test_documents()
    chunks = DocumentChunkingService().chunk_documents(documents)
    repository.upsert(chunks, EmbeddingGemmaEmbedding())
    print(f"Indexed {len(chunks)} chunks from {len(documents)} synthetic Markdown files.")


if __name__ == "__main__":
    main()
