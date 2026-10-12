# Architecture

## Local demo

- **Frontend:** Vite, React, TypeScript, React Router, and Tailwind CSS. TanStack Query manages server reads and cache state; `src/api/client.ts` centralizes HTTP transport and authentication headers.
- **Backend:** FastAPI, SQLAlchemy, and Pydantic. Routers handle HTTP, services apply workflow rules, and models map the existing MySQL schema.
- **Database:** MySQL 8+, using the supplied contract in `database/schema.sql`; the connected database remains authoritative if it differs.
- **Files:** Local storage beneath `backend/.uploads/`, with attachment metadata in MySQL.
- **Notifications and background work:** Console logging and in-process work for local demonstration only.

## Boundaries

- Do not create or migrate schema during application startup. Load `database/schema.sql` and the optional synthetic `database/seed_demo.sql` explicitly for a local demo database.
- Backend authorization and validation are authoritative. Frontend checks provide immediate feedback only.
- Cloud hosting, production email, object storage, durable workers, and production operations are tracked in `ProductionUpdate.md` and remain outside local-demo scope.
