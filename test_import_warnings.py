"""Catch dependency warnings during the application's embedding imports."""

import subprocess
import sys
import unittest
from unittest.mock import MagicMock

from backend.services.embedding_service import EMBEDDING_DIMENSIONS, EmbeddingGemmaEmbedding


class ImportWarningTests(unittest.TestCase):
    def test_embedding_imports_without_unsupported_pydantic_fields(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import warnings; "
                "warnings.filterwarnings('error', message=\"The 'validate_default' attribute.*\"); "
                "import backend.services.rag_service",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_embedding_adapter_preserves_query_and_document_encoding(self):
        embedding = EmbeddingGemmaEmbedding()
        embedding._model = MagicMock()
        embedding._model.encode.return_value = [0.25] * EMBEDDING_DIMENSIONS

        self.assertEqual(len(embedding.get_query_embedding("leave?")), EMBEDDING_DIMENSIONS)
        embedding._model.encode.assert_called_with(
            "leave?", prompt_name="Retrieval-query", normalize_embeddings=True
        )

        self.assertEqual(len(embedding.get_text_embedding("title: Leave | text: Policy")), EMBEDDING_DIMENSIONS)
        embedding._model.encode.assert_called_with(
            "title: Leave | text: Policy", normalize_embeddings=True
        )


if __name__ == "__main__":
    unittest.main()
