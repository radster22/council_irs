---
name: requirements-audit
description: Audit an application change against the standalone business rules and live database contract.
---

# Requirements Audit

Use for requirement reviews, feature planning, acceptance checks, or changes that affect product behavior. The complete, standalone requirements catalog is [02-business-rules.md](../../rules/02-business-rules.md). It is the only product-requirements source agents need.

## Source handling

1. Use `.claude/rules/02-business-rules.md` as the self-contained source of product requirements, obligation strength, acceptance criteria, and application scope.
2. Do not assume additional requirements from unavailable source material or add scope based on proposed implementation details.
3. Use [04-database-contract.md](../../rules/04-database-contract.md) for persistence constraints. A product requirement does not authorize a schema change.

## Audit procedure

1. Identify impacted BR IDs and acceptance criteria in the complete standalone requirements file.
2. Trace each requirement across frontend behavior, backend enforcement, persistence, and tests. Cite concrete file/function evidence; a green UI control alone is not backend enforcement.
3. Keep product behavior distinct from production stack changes listed in `ProductionUpdate.md`.
4. Change the requirements catalog only when a requirement is clarified or changed. Run relevant checks and report blockers as unverified, never as passing.
