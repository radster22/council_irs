---
name: budget-validate
description: Implement or review budget grid arithmetic and configured reconciliation against BR-008 and BR-022.
---

# Budget Validation

Use for budget-entry, total, balance, or budget-related submission work. Read [business rules](../../rules/02-business-rules.md) and [database contract](../../rules/04-database-contract.md) first.

## Procedure

1. Confirm the submission's published form template and its configured `budget_reconciliation.target`. The form must define any required sum; there is no universal balance target.
2. Treat client totals as display-only. Calculate each total and reconciliation result on the backend.
3. Use `Decimal` from validated decimal input through persistence/response; do not convert currency through binary floating point.
4. Enforce the 1–100 line-item range on server writes and keep line numbers unique per submission. Respect DB constraints and `RESTRICT` relationships.
5. Keep draft saving distinct from final-submission validation. On submission, return actionable errors and do not create a submitted snapshot when configured checks fail.
6. Update focused service/API tests for exact arithmetic, configured targets, no-target behavior, zero and boundary values, 100/101 lines, and invalid amounts as applicable.
7. Run focused backend tests, then broader checks when shared behavior changed. Record any tool startup failure as unverified.

Do not silently normalize entered amounts or create a balancing target not specified by the form.
