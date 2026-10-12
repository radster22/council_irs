# Architecture Rules

- Keep HTTP concerns in routers, persistence concerns in `db` and `models`, and business rules in `services`.
- Put request and response contracts in `schemas` and reusable UI contracts in `frontend/src/types`.
- Keep background and scheduled work in `backend/app/tasks`.
- Add or update tests when changing an API contract or business rule.
- Read and follow `.claude/settings.json`, `.claude/rules/*.md`, and the relevant `.claude/skills/*.md` before making any repo change.
- Prefer the existing project structure and naming over creating parallel modules or duplicate implementations.
- Treat the live MySQL database as the source of truth when it differs from repo-local fixtures or documentation.
- Use read-only schema inspection before implementing ORM models or database logic; do not change the database schema without explicit approval.