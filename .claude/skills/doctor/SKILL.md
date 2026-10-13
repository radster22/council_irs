---
name: doctor
description: Diagnose local setup and verification blockers without exposing secrets or changing live data.
---

# Local Demo Doctor

Use when a clone cannot start, connect, or run checks. Read [architecture](../../rules/01-architecture.md), [database contract](../../rules/04-database-contract.md), and [verification rules](../../rules/05-verification.md) as relevant.

## Procedure

1. Check repository files, dependency manifests, documented commands, and `.env.example` variable names/placeholders. Never open, echo, or print `.env` contents.
2. Inspect the environment without exposing values. Distinguish missing tools/dependencies from invalid or unavailable services.
3. Run the smallest check that demonstrates the issue. A command that fails to start is a blocker, not a passing check.
4. For a database issue, confirm whether the target is a disposable local demo DB; use read-only checks for diagnosis. Do not reset, migrate, or seed a database unless explicitly requested and the target is confirmed local/disposable.
5. Give concrete remediation steps based on repository docs. Avoid personal machine paths and secret-bearing command output.

## Report

List the check and result, what remains unverified, and the next safe step. Do not claim live MySQL compatibility from SQLite tests or checked-in DDL alone.
