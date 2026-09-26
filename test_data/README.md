# Synthetic HR document fixtures

These files describe **ExampleCo**, a fictional company. Every person, policy, amount, and event is invented for local retrieval and access-control testing. No file contains real employee data or legal advice.

| File | Suggested document type | Classification | Owner |
| --- | --- | --- | --- |
| `company_handbook.md` | `hr_policy` | INTERNAL | — |
| `leave_and_attendance_policy.md` | `hr_policy` | INTERNAL | — |
| `benefits_enrolment_guide.md` | `hr_policy` | INTERNAL | — |
| `manager_leave_approval_guide.md` | `manager_policy` | CONFIDENTIAL · HR | — |
| `onboarding_checklist.md` | `hr_policy` | INTERNAL | — |
| `payroll_close_runbook.md` | `payroll_runbook` | RESTRICTED · PAYROLL | — |
| `payslip_alice_2026_08.md` | `payslip` | RESTRICTED · PAYROLL | `alice` |
| `payslip_marcus_2026_08.md` | `payslip` | RESTRICTED · PAYROLL | `marcus` |
| `payroll_register_2026_08.csv` | payroll register fixture | RESTRICTED · PAYROLL | — |

The Markdown fixtures include the document metadata used by the existing in-memory corpus. The CSV is a separate reconciliation fixture; `payroll_register` is not an allowed document type in the current app policy. The app does **not** load files from this directory automatically. Its active demo corpus remains in `seed/demo_data.py`.

The August register reconciles to the two payslips: gross HKD 97,000, MPF deductions HKD 3,000, optional benefit deductions HKD 1,030, and net HKD 92,970. Alice's figures match the existing demo payslip.

The fixture topics were informed by public examples of [absence-policy coverage](https://www.acas.org.uk/creating-absence-policies), [induction checklists](https://www.acas.org.uk/template-checklist-for-induction-of-new-staff), and [payroll record fields](https://www.dol.gov/sites/dolgov/files/WHD/legacy/files/FLSA-MSPA-H2A-091925-Public.pdf). The text and rules here are original and fictional; those sources are not the policies of ExampleCo.
