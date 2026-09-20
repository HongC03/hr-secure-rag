"""Index the synthetic demo corpus in pgvector; never use this script for real data without approvals."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.repositories.pgvector_repository import PgVectorRepository
from backend.services.chunking_service import DocumentChunkingService
from backend.services.embedding_service import EmbeddingGemmaEmbedding
from seed.demo_data import DOCUMENTS

repository = PgVectorRepository.from_environment()
if not repository:
    raise SystemExit("Set PGVECTOR_DATABASE_URL before seeding.")
chunks = DocumentChunkingService().chunk_documents(DOCUMENTS)
repository.upsert(chunks, EmbeddingGemmaEmbedding())
print(f"Indexed {len(chunks)} synthetic document chunks in pgvector.")
