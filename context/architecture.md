# Architecture

## Overview

- `backend/app`: Python API, persistence, domain services, and background tasks.
- `frontend/src`: browser application, API client, shared components, forms, and routes.
- `database`: initial relational schema and local seed data.
- `context`: requirements, architecture notes, and source artifacts.

The backend owns validation and budget calculations. The frontend presents validated workflows and must not be the authoritative source for financial rules.

## Decisions To Confirm

- API framework and database engine/version for deployment.
- Authentication provider and role model.
- Upload storage, malware scanning, and retention policy.
- Production hosting, observability, backup, and recovery targets.