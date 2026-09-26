"""Load the synthetic Markdown fixtures for local pgvector experiments."""
from __future__ import annotations

from pathlib import Path
from typing import Any


TEST_DATA_DIR = Path(__file__).resolve().parents[1] / "test_data"
SUPPORTED_TYPES = {"hr_policy", "manager_policy", "payroll_runbook", "payslip", "tax_statement"}
REQUIRED_FIELDS = {"id", "title", "document_type", "classification", "owner_id", "tags"}


def load_test_documents(directory: Path = TEST_DATA_DIR) -> list[dict[str, Any]]:
    """Read the small, fixed front-matter format used by test_data/*.md."""
    documents: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError(f"{path}: expected a YAML-style metadata header")
        header, content = text[4:].split("\n---\n", 1)
        metadata: dict[str, str] = {}
        for line in header.splitlines():
            key, separator, value = line.partition(":")
            if not separator:
                raise ValueError(f"{path}: invalid metadata line: {line}")
            metadata[key.strip()] = value.strip()
        missing = REQUIRED_FIELDS - metadata.keys()
        if missing:
            raise ValueError(f"{path}: missing metadata: {', '.join(sorted(missing))}")
        if metadata["document_type"] not in SUPPORTED_TYPES:
            raise ValueError(f"{path}: unsupported document_type: {metadata['document_type']}")
        if metadata["id"] in seen_ids:
            raise ValueError(f"{path}: duplicate id: {metadata['id']}")
        seen_ids.add(metadata["id"])
        tags = metadata["tags"]
        if not tags.startswith("[") or not tags.endswith("]"):
            raise ValueError(f"{path}: tags must be a bracketed list")
        owner_id = None if metadata["owner_id"] == "null" else metadata["owner_id"]
        if metadata["document_type"] in {"payslip", "tax_statement"} and not owner_id:
            raise ValueError(f"{path}: payroll and tax records need an owner_id")
        if not content.strip():
            raise ValueError(f"{path}: content is empty")
        documents.append({
            "id": metadata["id"],
            "title": metadata["title"],
            "document_type": metadata["document_type"],
            "classification": metadata["classification"],
            "owner_id": owner_id,
            "tags": [tag.strip().strip("\"'") for tag in tags[1:-1].split(",") if tag.strip()],
            "content": content.strip(),
        })
    return documents
