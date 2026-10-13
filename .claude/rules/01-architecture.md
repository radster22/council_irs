# Architecture and Scope

## Runtime architecture

- Frontend: Vite, React 18, TypeScript, React Router, Tailwind CSS, and TanStack Query. Reuse `frontend/src/api/client.ts`, existing auth/query hooks, types, and shared components.
- Backend: FastAPI, SQLAlchemy 2, and Pydantic v2. Keep HTTP concerns in routers, workflow rules in services, persistence in `models`/DB access, and request/response contracts in schemas.
- Database: MySQL 8+ and the existing `council_irs_db` contract. Never create or migrate schema at application startup.
- Files: local filesystem under repository-root `.uploads/`, with attachment metadata in MySQL. Uploaded files are added through the UI and remain local/ignored by Git.
- Notifications: console logging. Background work: lightweight in-process tasks.

## Local/production boundary

The local demo uses MySQL, filesystem uploads, console notifications, and in-process tasks. It does not prove cloud authorization, FedRAMP/NIST compliance, production capacity/availability, perpetual retention operations, incident response, email delivery, vendor support, backup/recovery, or delivery schedule. Any production deployment must follow the hosting and compliance boundary in BR-026; deployment infrastructure remains outside this local-demo scope.

Do not add cloud services, managed secrets, object storage, durable queues, production mail, or operational controls as part of a local feature by assumption.
