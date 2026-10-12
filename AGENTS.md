# NYC Council Initiative Reporting System

## Goal

Build a local demonstration application for NYC Council Initiative Reporting System RFP PIN #102202709162026.

## Architecture

* Frontend: Vite, React 18, TypeScript, React Router, Tailwind CSS.
* Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2.
* Database: Existing MySQL 8+ schema `council_irs_db`.
* File storage: Local filesystem under `.uploads/`, with metadata in MySQL.
* Notifications: Console logging.
* Background work: Lightweight in-process tasks only.

## Non-Negotiable Rules

1. Treat the live MySQL schema as authoritative. `database/schema.sql` is absent; do not fabricate or modify database schema or triggers unless explicitly requested.
2. Preserve composite foreign-key integrity, historical submission versions, and audit-log immutability.
3. Enforce authentication, role authorization, and organization-level access on the backend.
4. Use `Decimal`-based arithmetic for monetary calculations; never use floating-point arithmetic for budgets.
5. Enforce a maximum of 100 budget line items and validate budget reconciliation before submission.
6. Never trust client-supplied totals, user roles, organization IDs, or submission permissions.
7. Validate uploads, enforce the 25 MiB limit, and prevent path traversal.
8. Never commit credentials, local uploads, database dumps, or generated secrets.

## Project Guidance

* Read `context/rfp-functional-specs.md` for functional requirements.
* Read `context/db-schema-reference.md` for tables, constraints, and triggers.
* Read `.claude/rules/04-business-rules.md` for confirmed RFP business rules and the requirement-source hierarchy.
* Follow applicable files in `.claude/rules/`.
* Use `.claude/skills/` for reusable project checks.
* Record deferred production infrastructure and migration requirements in `ProductionUpdate.md`.

## Requirement Sources

The RFP is the source for contractual requirements. `business_rules/NYC_Council_Initiative_Reporting_User_Stories_and_Business_Rules.xlsx` is a traceability aid; validate its rule summaries against the cited RFP text when a conflict matters. The high-level architecture document is a proposed design, not an independent contractual requirement. Keep local-demo constraints and production-only obligations distinct, and record deferred production requirements in `ProductionUpdate.md`.

## Local Commands

* Backend: `cd backend && uvicorn app.main:app --reload --port 8000`
* Frontend: `cd frontend && npm run dev`
* Backend tests: `pytest backend/tests`
* Frontend checks: `cd frontend && npm run lint && npm run build`
* Frontend tests: no test script is configured yet; add the test runner and script before relying on `npm test`.

## Implementation Discipline

Implement in small, testable increments. Run relevant tests after changes. Do not introduce production infrastructure or expand scope without explicit approval.

Before editing any file, read the applicable `.claude/rules/*.md` and matching `.claude/skills/*.md`, and run the relevant repo checks from the project hook workflow. Follow those instructions every time; do not skip them for convenience.

## Phase Tracker

Use the following phases to track progress. Once a phase is complete, update the line to strikethrough format and add a brief note, for example: `~~Phase 1 — Local infrastructure — completed: MySQL, FastAPI, MinIO, and Mailpit verified locally~~`.

- ~~Phase 1 — Local infrastructure — MySQL · SQLAlchemy · FastAPI — completed: local MySQL connection, `SELECT 1`, and read-only schema inspection verified; MinIO and Mailpit are out of local-demo scope.~~
- ~~Phase 2 — Backend foundations — SQLAlchemy · Pydantic · JWT · RBAC — completed: ORM columns, constraints, and indexes match live metadata; database-backed login, role guards, and organization membership checks are implemented and tested.~~
- [ ] Phase 3 — Reporting workflow — Initiatives · Cycles · Dynamic forms · Budget grid — support draft/save/submit flows with file attachments and review state.
- [ ] Phase 4 — Frontend — React · TypeScript · React Router · TanStack Query — build login, dashboards, report editor, history, and council review screens.
- [ ] Phase 5 — Supporting features — MinIO · Excel/CSV/PDF · Email · Background jobs — add exports, notifications, reminders, and scheduled work.

### Verification Notes

The complete live contract is recorded in `context/db-schema-reference.md`; metadata was queried read-only and no database changes were made. Authentication and access-control tests use an isolated SQLite fixture. A successful login using a real MySQL application user remains unverified; do not use production or personal credentials for tests.

### Completion Rule

When a task is finished, do not leave it as an unchecked item. Replace it using strikethrough formatting so the completed work is clearly visible to future agents, for example:

- ~~Phase 3 — Reporting workflow — completed: draft/save/submit flow and budget validation are in place.~~
