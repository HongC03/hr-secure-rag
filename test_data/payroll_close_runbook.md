---
id: payroll-close-runbook-2026
title: ExampleCo Monthly Payroll Close Runbook
document_type: payroll_runbook
classification: RESTRICTED · PAYROLL
owner_id: null
tags: [payroll, close, reconciliation, approval]
---

# ExampleCo Monthly Payroll Close Runbook

Effective date: 1 August 2026. Owner: Payroll Operations. This is a fictional test document.

## Cutoff and inputs

The sample monthly cutoff is 17:00 Hong Kong time on the 25th. Payroll collects approved time corrections, leave entries, starter and leaver changes, and voluntary benefit elections from the private HR portal. An unapproved change is held for review rather than silently added to the run.

## Reconciliation

For each employee, compare the gross amount with approved compensation data, calculate each named deduction, and check that net pay equals gross pay minus total deductions. Sum the employee rows and compare the totals with the payroll register. The August fixture has gross HKD 97,000, MPF deductions HKD 3,000, optional benefit deductions HKD 1,030, and net HKD 92,970.

## Approval and release

One payroll operator prepares the run and a different authorized approver reviews the reconciliation and exception list. The operator records both approvals before release. Payslips are sent only to each employee's private portal inbox. A corrected run gets a new version and retains the prior version in the audit trail.

## Access and exceptions

Payroll staff investigate a disputed amount through the approved case queue. Managers may receive a scheduling question but do not receive employee pay details. Never export restricted records to an unapproved tool. These steps are demonstration data, not a real payroll procedure.
