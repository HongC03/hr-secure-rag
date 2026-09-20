"""Document storage boundary for the synthetic in-memory demonstration corpus."""
from __future__ import annotations

import uuid
from typing import Any


class InMemoryDocumentRepository:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        # Keep the supplied list to make the demo corpus easy to inspect and
        # retain backwards compatibility with the exported DOCUMENTS fixture.
        self._documents = documents

    def all(self) -> list[dict[str, Any]]:
        return list(self._documents)

    @property
    def documents(self) -> list[dict[str, Any]]:
        """Compatibility view for the synthetic demo fixture."""
        return self._documents

    def create_payslip(self, title: str, content: str, owner_id: str) -> dict[str, Any]:
        document = {
            "id": "pay-" + str(uuid.uuid4())[:8],
            "title": title,
            "document_type": "payslip",
            "classification": "RESTRICTED · PAYROLL",
            "owner_id": owner_id,
            "content": content,
            "tags": ["payslip", "payroll"],
        }
        self._documents.append(document)
        return document
