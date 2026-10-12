---
name: rollover-test
description: Design and run focused tests for fiscal-year budget rollover behavior.
---

# Rollover Testing

Identify the rollover rules from the functional specifications, then cover normal rollover, zero balances, boundary dates, invalid source data, and repeat execution. Verify idempotency if required by the specification. Do not assume policy rules that are not documented.

## Required verification

- Check whether the reporting cycle or fiscal-year boundary is the authoritative rollover trigger.
- Cover both valid rollover and invalid source conditions.
- Validate that repeated execution does not double-count or mutate source totals unexpectedly.
- Keep assertions focused on the business rule, not on incidental formatting.