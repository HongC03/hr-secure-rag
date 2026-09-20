"""Local smoke test for Google EmbeddingGemma.

Before running this script, accept the model license on Hugging Face and run
``hf auth login``. The first run downloads the model; later runs use its local
cache and can run offline.
"""

import torch
from sentence_transformers import SentenceTransformer


MODEL_ID = "google/embeddinggemma-300M"
EMBEDDING_DIMENSIONS = 768


def device_for_embedding() -> str:
    """Prefer Apple Silicon's Metal backend, falling back to CPU."""
    return "mps" if torch.backends.mps.is_available() else "cpu"


def main() -> None:
    device = device_for_embedding()
    model = SentenceTransformer(MODEL_ID, device=device)

    query_embedding = model.encode(
        "How much parental leave do I receive?",
        prompt_name="Retrieval-query",
        normalize_embeddings=True,
    )
    document_embedding = model.encode(
        "Employees receive 16 weeks of paid parental leave.",
        prompt="title: Parental Leave Policy | text: ",
        normalize_embeddings=True,
    )

    print(f"Device: {device}")
    print(f"Query dimensions: {query_embedding.shape}")
    print(f"Document dimensions: {document_embedding.shape}")

    if query_embedding.shape != (EMBEDDING_DIMENSIONS,):
        raise RuntimeError("Query embedding has an unexpected dimension.")
    if document_embedding.shape != (EMBEDDING_DIMENSIONS,):
        raise RuntimeError("Document embedding has an unexpected dimension.")


if __name__ == "__main__":
    main()
