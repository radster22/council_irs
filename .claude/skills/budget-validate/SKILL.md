---
name: budget-validate
description: Validate budget input structure and arithmetic against repository rules.
---

# Budget Validation

Validate input shape, required identifiers, nonnegative amounts where required, totals, and rollover behavior. Use decimal arithmetic and the documented functional requirements. Report discrepancies with the affected field or calculation; do not silently rewrite source values.

## Required checks

- Confirm the list length is within the repo maximum (100 items unless a stricter rule is documented).
- Convert all amounts to `Decimal` before arithmetic.
- Reject missing categories, invalid numeric values, negative amounts, and mismatched totals.
- Add or update unit tests for each boundary that is intended to be supported.
- Surface the exact error messages to the caller instead of rewriting the payload silently.