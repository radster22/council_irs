# Budget Calculation Rules

- Use decimal arithmetic for currency; do not use binary floating-point for financial totals.
- Preserve source amounts and report calculated values separately where practical.
- Make rounding and rollover behavior explicit, deterministic, and covered by tests.
- Reject invalid or internally inconsistent budget inputs with actionable validation errors.
- Validate sums, totals, and budget rows on the server; never trust client-submitted totals.
- Enforce the repository maximum of 100 budget line items unless the actual schema requires a different rule.
- Add regression tests for zero, one, boundary, and invalid totals before shipping monetary logic changes.