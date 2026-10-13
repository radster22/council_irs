# Agent Instructions

Build and maintain a local demonstration of the NYC Council Initiative Reporting System for RFP PIN #102202709162026.

## Canonical project guidance

`.claude/rules/` contains focused technical guidance. [02-business-rules.md](.claude/rules/02-business-rules.md) is the single source of truth for application requirements. Read applicable guidance and the matching `.claude/skills/*/SKILL.md` before editing. Do not create duplicate requirement catalogs.

- [Architecture and local/production boundary](.claude/rules/01-architecture.md)
- [Application business rules](.claude/rules/02-business-rules.md)
- [Security requirements](.claude/rules/03-security.md)
- [Database contract](.claude/rules/04-database-contract.md)
- [Verification and change discipline](.claude/rules/05-verification.md)
- [Production-only work register](ProductionUpdate.md)

Treat all product requirements, obligation strengths, and acceptance details in `.claude/rules/02-business-rules.md` as complete and standalone. `ProductionUpdate.md` covers only production technology changes.

## Stack and boundaries

- Frontend: Vite, React 18, TypeScript, React Router, Tailwind CSS, TanStack Query.
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic v2.
- Database: MySQL 8+, schema `council_irs_db`; the connected live schema is authoritative.
- Local file storage: repository-root `.uploads/`; notifications are logged; background work is in-process.
- Do not add production infrastructure or change the existing database contract unless explicitly requested.

## Working method

1. Inspect the affected UI, API, service, ORM, tests, and applicable rules before changing behavior.
2. Keep HTTP concerns in routers, business rules in services, persistence in models/DB access, and shared client behavior in existing frontend utilities.
3. Make a small cohesive change and reuse existing dependencies and helpers. Do not add libraries for functionality already available in the project.
4. For behavior changes, update focused tests. Run relevant checks and report exactly what passed, failed, or could not start.
5. Never describe an unrun or blocked check as passing. Do not use a live database for destructive work.
6. Before a Claude Code `git commit`, `.claude/settings.json` runs the configured repository checks. The hook blocks the commit if a check fails.
7. Update `.claude/rules/02-business-rules.md` when a product requirement is clarified or changed. Keep production technology transition details in `ProductionUpdate.md`.

## Local commands

```powershell
# From repository root
python -m compileall -q backend/app
python -m pytest backend/tests -q

# Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
npm run lint
npm test -- --run
npm run build
```

Copy the root `.env.example` to `.env` for local configuration. Never read, print, or commit `.env` values, real credentials, generated secrets, uploads, or database dumps.
