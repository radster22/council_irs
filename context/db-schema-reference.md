# Database Schema Reference

## Verification Status

The live `council_irs_db` schema was inspected using read-only `INFORMATION_SCHEMA` SELECTs: 95 column rows, 59 key-usage rows, 56 index rows, 18 foreign keys, and 7 triggers. The application connection also passed `SELECT 1`. No table, trigger, or application data was modified. `database/schema.sql` is absent; use the live database as the source of truth.

The ORM in `backend/app/models/` matches the live table names, columns, types, and nullability. Primary, unique, and foreign-key columns, including their composite order, were compared against the live metadata with no mismatches.

## Tables

- `organizations`: EIN, legal name, organization type, borough, and status.
- `initiatives`: code, name, fiscal year, and lifecycle status.
- `initiative_relationships`: predecessor/successor links with `RENAMED` or `COMBINED` type.
- `reporting_cycles`: initiative, cycle name, start/due dates, and status.
- `initiative_organizations`: composite initiative/organization membership and awarded amount.
- `form_templates`: initiative-scoped versioned JSON schema and publish state.
- `users`: email, password hash, name, role, and active state.
- `user_organizations`: composite user/organization membership and primary flag.
- `submissions`: initiative, organization, cycle, template version, state, form data, and budget totals.
- `budget_line_items`: numbered budgeted and actual amounts per submission.
- `submission_versions`: immutable form/budget snapshots and review notes.
- `attachments`: bucket/object key, original filename, content type, byte size, checksum, and uploader.
- `audit_logs`: append-only submission state changes and actor metadata.

## Integrity and Triggers

- `submissions` preserves composite foreign keys to the matching initiative/cycle, initiative/template version, and initiative/organization pair.
- `submission_versions` references the matching submission/template version pair.
- All inspected foreign keys use `ON DELETE RESTRICT` and `ON UPDATE NO ACTION`.
- Named non-unique indexes are `idx_audit_sub`, `idx_audit_time`, `idx_init_fy`, `idx_sub_triage` (`is_balanced`, `status`), and `idx_user_role`; all primary, unique, foreign-key, and supporting index columns match the live metadata.
- Triggers prevent update/delete on `audit_logs`, prevent update/delete on `submission_versions`, block schema changes while a template remains published, and enforce at most one primary user-organization link.
- Do not add ORM delete cascades or issue DDL against the live schema.

## Authentication Verification

The API authenticates against `users.email`, `users.password_hash`, and `users.is_active`; roles come from the database, not client input or token claims. Unit tests use an isolated in-memory SQLite database. A successful login against an actual MySQL user account has not been exercised.