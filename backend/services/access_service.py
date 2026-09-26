from typing import Any


class AccessService:
    """The policy enforcement point; every unlisted document type is denied."""

    CLASSIFICATION_BY_TYPE = {
        "payslip": "RESTRICTED · PAYROLL",
        "tax_statement": "RESTRICTED · TAX",
        "payroll_runbook": "RESTRICTED · PAYROLL",
        "manager_policy": "CONFIDENTIAL · HR",
        "hr_policy": "INTERNAL",
    }

    def metadata_is_valid(self, document: dict[str, Any]) -> bool:
        kind = document.get("document_type")
        expected = self.CLASSIFICATION_BY_TYPE.get(kind)
        if expected is None or document.get("classification") != expected:
            return False
        owner = document.get("owner_id")
        if kind in {"payslip", "tax_statement"}:
            return isinstance(owner, str) and bool(owner)
        return owner is None

    def can_read(self, user: dict[str, str], document: dict[str, Any]) -> bool:
        if not self.metadata_is_valid(document):
            return False
        kind = document["document_type"]
        if kind in {"payslip", "tax_statement"}:
            return document["owner_id"] == user["id"] or user["role"] == "hr_payroll"
        if kind == "payroll_runbook": return user["role"] == "hr_payroll"
        if kind == "manager_policy": return user["role"] in {"manager", "hr_partner", "hr_payroll"}
        return kind == "hr_policy"

    def allowed_documents(self, user: dict[str, str], documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [document for document in documents if self.can_read(user, document)]
