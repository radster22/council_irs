# Database Contract

The connected live MySQL schema is authoritative. Inspect it read-only before making database-dependent claims. The checked-in `database/schema.sql` is a repository setup artifact, not proof that a connected database matches it and not permission to alter the live schema.

## Existing tables

- `organizations`: EIN, legal name, organization type, borough, status.
- `initiatives`: code, name, fiscal year, lifecycle status.
- `initiative_relationships`: predecessor/successor and `RENAMED`/`COMBINED` lineage.
- `reporting_cycles`: initiative, cycle name, start/due dates, status.
- `initiative_organizations`: initiative/organization eligibility and awarded amount.
- `form_templates`: initiative-scoped versioned JSON form schema and publish state.
- `users`: email, password hash, full name, role, active state.
- `user_organizations`: user/organization membership and primary flag.
- `submissions`: initiative, organization, cycle, template version, state, form data, and budget totals.
- `budget_line_items`: numbered budget/actual amounts per submission.
- `submission_versions`: immutable form/budget snapshots and reviewer notes.
- `attachments`: storage reference, filename/type/size/checksum, uploader.
- `audit_logs`: submission event, actor, role, JSON state diff, timestamp.

## Integrity rules to preserve

- Submission composite FKs bind initiative to its cycle, eligible organization, and form-template version.
- Submission-version composite FK binds a snapshot to the submission's exact template version.
- Budget line number is bounded 1–100; attachment is limited to 26,214,400 bytes (25 MiB).
- Audit logs and submission versions are append-only through database triggers; published template schema cannot be edited in place while published; one primary organization per user is enforced.
- Existing keys use restrictive delete behavior. Do not add ORM delete cascades or issue schema DDL as an application workaround.

## ORM and verification

ORM models must map the existing columns, nullability, keys, indexes, composite foreign keys, and delete/update rules. Check `backend/app/models/` and contract tests before changing persistence. SQLite fixtures can test application logic, but cannot prove compatibility with MySQL JSON, ENUM, checks, triggers, or actual connected metadata.

Previous recorded read-only inspection reported 95 column rows, 59 key-usage rows, 56 index rows, 18 foreign keys, and 7 triggers; earlier metadata comparison reported no ORM mismatch and `SELECT 1` succeeded. This is historical evidence, not a fresh connection check. No successful live MySQL comparison is recorded for the current review. Do not claim otherwise.

Application authentication uses `users.email`, `password_hash`, and `is_active`; role/identity must come from the database. Use the synthetic `database/seed_demo.sql` only against an explicitly disposable local demo database.
