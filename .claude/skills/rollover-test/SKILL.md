---
name: rollover-test
description: Plan or test annual initiative/report/form rollover and historical lineage requirements BR-015 and BR-016.
---

# Annual Rollover and Lineage

Use when designing, reviewing, or implementing year-to-year portfolio behavior. Read [business rules](../../rules/02-business-rules.md) and [database contract](../../rules/04-database-contract.md). Test behavior against the stated requirements without assuming unstated rollover policies.

## Required behavior to trace

- BR-015 / RFP pp. 9–10: authorized Council Finance users can duplicate prior-year reporting structure/forms; standard and initiative-specific questions and layouts carry forward.
- BR-016 / RFP p. 10: renamed or combined initiatives keep links to predecessor initiatives and historical reports.
- Form versions and prior submissions remain historically stable. Never edit published schema or historical snapshots in place; preserve existing composite foreign keys and lineage.

## Test plan

1. Define source fiscal year, destination fiscal year, copied entities, and which identities/relationships must remain new versus linked.
2. Verify copied configuration/layout, with old published templates/submissions unchanged.
3. Verify renamed and combined predecessor/successor lineage and authorization on the operation.
4. Cover empty portfolio, invalid source, duplicate destination, and repeat execution only after expected behavior is defined. Do not assume an idempotency policy.
5. Verify records and joins against the existing schema. No migration/schema edit is implied by these requirements.
