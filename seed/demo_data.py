"""Synthetic identities and documents; never replace with real HR data."""

USERS = {
    "alice": {"name": "Alice Chan", "role": "employee", "department": "Product", "label": "Employee — own records only"},
    "marcus": {"name": "Marcus Lee", "role": "manager", "department": "Product", "label": "Manager — no payroll access"},
    "priya": {"name": "Priya Shah", "role": "hr_payroll", "department": "People", "label": "HR Payroll — approved payroll access"},
    "olivia": {"name": "Olivia Wong", "role": "hr_partner", "department": "People", "label": "HR Partner — HR policies, no payroll access"},
}

# This corpus is deliberately fictional and exists only for local demo/testing.
DOCUMENTS = [
    {"id": "pay-alice-2026-08", "title": "August 2026 payslip — Alice Chan", "document_type": "payslip", "classification": "RESTRICTED · PAYROLL", "owner_id": "alice", "content": "Employee: Alice Chan. Period: August 2026. Gross monthly pay: HKD 42,000. Mandatory provident fund employee contribution: HKD 1,500. Net pay: HKD 39,870. This record is synthetic.", "tags": ["payslip", "august", "pay", "mpf"]},
    {"id": "tax-alice-2025", "title": "Tax statement — Alice Chan", "document_type": "tax_statement", "classification": "RESTRICTED · TAX", "owner_id": "alice", "content": "Tax year 2025. Employee: Alice Chan. This synthetic statement is visible only to the employee and authorised HR Payroll staff.", "tags": ["tax", "statement", "employee"]},
    {"id": "benefits-open-enrolment", "title": "Open-enrolment benefits guide", "document_type": "hr_policy", "classification": "INTERNAL", "owner_id": None, "content": "All employees may review the open-enrolment guide. Submit benefit elections through the approved HR portal. Do not send personal health information through chat.", "tags": ["benefits", "enrolment", "policy"]},
    {"id": "manager-leave-guide", "title": "Manager leave-approval guide", "document_type": "manager_policy", "classification": "CONFIDENTIAL · HR", "owner_id": None, "content": "Managers may review leave requests for their direct reports. Payroll, tax, compensation, disciplinary, and medical documents are outside manager access unless separately approved.", "tags": ["manager", "leave", "approval"]},
    {"id": "payroll-close-runbook", "title": "Payroll close runbook", "document_type": "payroll_runbook", "classification": "RESTRICTED · PAYROLL", "owner_id": None, "content": "Payroll operators reconcile approved time records, validate exceptions, use dual approval before release, and retain a tamper-evident audit trail. Never export records to unapproved tools.", "tags": ["payroll", "close", "approval", "runbook"]},
]
