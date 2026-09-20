from typing import Any


class AccessService:
    """The policy enforcement point; every unlisted document type is denied."""

    def can_read(self, user: dict[str, str], document: dict[str, Any]) -> bool:
        kind = document["document_type"]
        if kind in {"payslip", "tax_statement"}:
            return document["owner_id"] == user["id"] or user["role"] == "hr_payroll"
        if kind == "payroll_runbook": return user["role"] == "hr_payroll"
        if kind == "manager_policy": return user["role"] in {"manager", "hr_partner", "hr_payroll"}
        return kind == "hr_policy"

    def allowed_documents(self, user: dict[str, str], documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [document for document in documents if self.can_read(user, document)]
