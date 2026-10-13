# Project Diagnostics

**Review date:** 2026-10-13
**Scope:** Current repository source, project instructions and skills, database setup/seed scripts, frontend, backend, and available verification commands.

## Scope and limits

This audit uses `.claude/rules/02-business-rules.md` as the standalone product-requirements source and follows the files named in `AGENTS.md`. The requirements are assessed against the current code; source business documents are not needed for this review. No `.env` values, upload contents, database dumps, or real credentials were read. No live MySQL connection was attempted, so this report does not certify the connected database or a fresh deployment.

The worktree already contained unrelated edits and deletions when this review began. This audit did not edit application code, the schema, the seed, or existing guidance. This report is the only intentional source-file addition for this audit.

## Executive summary

The project has a working local-demo foundation: database-backed login and report workflows, external organization scoping, draft persistence, server-side decimal budget calculations, submission snapshots, reviewer decisions, audit records, and root `.uploads/` storage. Frontend lint, tests, and production build pass.

The application is not yet compliant with the full business-rules SSOT. The largest functional gaps are Council configuration and user management, EIN validation/autofill, conditional/embedded form capabilities, Council editing of submitted reports, missing-obligation and incomplete-report triage, export/PDF/analytics, and file-content type validation. The seed also does not provide the open unstarted assignment promised by the README. Backend behavior remains unverified by executable tests in this environment, and live MySQL compatibility is unverified.

## Verification performed

| Check | Result |
| --- | --- |
| `python -m compileall -q backend/app` | **Could not start.** Windows Apps `python.exe` failed with “A specified logon session does not exist.” |
| `python -m pytest backend/tests -q` | **Could not start.** Same Python launcher failure; backend tests are unverified, not passing. |
| `npm run lint` from `frontend/` | **Passed.** TypeScript check completed. |
| `npm test -- --run` from `frontend/` | **Passed.** 2 test files, 50 tests. These are frontend tests with mocked API behavior, not end-to-end backend tests. |
| `npm run build` from `frontend/` | **Passed.** TypeScript project build and Vite production build completed. |
| Live MySQL metadata comparison / login | **Not performed.** The `.env` was not read and no database credentials were used. `test_model_contract.py` checks SQLAlchemy metadata statically; it does not connect to MySQL despite the `live_table_names` test name. |
| Runtime Claude commit hook | **Not run.** No commit was attempted. Its Python checks would currently hit the same launcher blocker. |

## Findings by priority

### High — required features and data integrity

1. **Council cannot configure the portfolio, reporting cycles, assignments, or forms through the application.** The database has the required entities and submitter reads use them, but there are no initiative, cycle, assignment, template, or form-builder routes/pages. `backend/app/routers/users.py` only exposes `GET /api/admin/users`; it does not add/manage users, change roles or organization memberships, or reset credentials. This leaves BR-001, BR-002, BR-004, BR-015, and BR-017 incomplete and also blocks application-based EIN registry management under BR-023/024.

2. **EIN validation and organization autofill are absent.** A submitter is associated with an organization through `user_organizations`, and eligibility is enforced against `initiative_organizations`; this is useful server-side scoping. There is no EIN entry/validation or organization-detail lookup/autofill UI/API, so BR-009, BR-023, and BR-024 are only partially addressed or missing.

3. **The form renderer supports only a subset of the configured form model.** Submission schemas are read from a published JSON template, and backend submit-time validation handles supported field types. The editor flattens fields and does not render section names/help text, branching/conditional behavior, or embedded tables. The backend validator does not evaluate conditional rules either. See `backend/app/routers/submissions.py:133-151`, `backend/app/services/submission_service.py:422-503`, and `frontend/src/routes/ReportEditorPage.tsx:260-295`. This leaves portions of BR-003/004/021 unimplemented.

4. **Draft autosave rejects incomplete monetary input.** The editor autosaves draft changes (`frontend/src/routes/ReportEditorPage.tsx:176-202`), but `persist_submission` always validates every budget amount before saving, even when `status` is `DRAFT` (`backend/app/services/submission_service.py:322-343`). A temporarily blank or malformed amount therefore prevents that draft save; `isDirty` stays true, so the autosave effect schedules another attempt. This weakens BR-013's save-and-resume behavior while users are editing.

5. **Council cannot edit submitted reports, and historical snapshots are not exposed in the portal.** `get_submission_for_user(..., write=True)` allows edits only in `DRAFT` or `REVISION_REQUESTED` (`backend/app/services/submission_service.py:303-319`), so an administrator cannot edit a submitted report as BR-019 requires. Submission versions are stored, but the detail response returns audit events only (`backend/app/routers/submissions.py:169-181`); the UI has no version/snapshot browser. `persist_submission` records audit rows for submissions, not draft edits (`backend/app/services/submission_service.py:388-414`).

6. **Reviewer triage cannot identify missing obligations or incomplete/invalid submissions.** The queue starts from existing non-draft submissions and filters by status, a text match over submission ID/initiative name/organization name/cycle name, and `is_balanced` (`backend/app/services/submission_service.py:130-180`). It cannot show eligible assignments with no submission, incomplete drafts, validation errors, or arbitrary submission-field queries. This is only a partial implementation of the oversight and triage requirements.

7. **Uploaded content is not type-validated.** `save_uploaded_file` enforces the 25 MiB limit, filename/path containment, and computes a checksum, but trusts `UploadFile.content_type` and stores arbitrary bytes (`backend/app/services/upload_service.py:32-79`). The UI file input also has no `accept` restriction. This does not meet BR-012's accepted Office/CSV/PDF types and content validation. The current root `.uploads/` path and download authorization/path containment are present.

8. **The seeded demo has no open unstarted report assignment.** `database/seed_demo.sql` assigns organizations to the active initiatives and seeds a submission for every eligible organization in each currently `OPEN` cycle. `list_available_reports` removes any assignment/cycle tuple that already has a submission (`backend/app/services/submission_service.py:74-93`). Therefore `/api/submissions/available` is empty after the seed, despite `README.md` claiming an “open unstarted assignment.” A reviewer cannot demonstrate starting a fresh report from this seed without changing local data.

### Medium — workflow, oversight, and usability

9. **Exports, PDF output, and analytics are not implemented.** There are no Excel/CSV export routes or UI, no grid-accurate PDF output, and no dashboard charts/visualizations. The report editor explicitly states PDF receipt/email delivery are unavailable (`frontend/src/routes/ReportEditorPage.tsx:414-419`), and the review page lists exports and administration as unavailable (`frontend/src/routes/ReviewPage.tsx:66`). These are explicit requirements in the SSOT, not only production-hosting changes.

10. **Confirmation is only a success message and an ID-only log; reminders are absent.** After persistence, the backend logs a submission ID (`backend/app/routers/submissions.py:259-260`) and the UI shows a receipt message. It does not send or log a confirmation containing the submitted information. Console logging is appropriate for local notification transport, but BR-014's confirmation content is not demonstrated; reminder scheduling/recipient configuration is also absent.

11. **The budget UI is a basic editable list rather than a full grid.** Server-side `Decimal` arithmetic, configured reconciliation, and the 100-line limit are implemented in `backend/app/services/budget_service.py` and `submission_service.py`. The UI has category and amount inputs, but no column headings, description, or actual-amount entry despite those columns existing in the database schema. Treat BR-008 as partial; BR-022's core calculation and configured-target behavior is present.

12. **API errors are surfaced as raw response text.** `frontend/src/api/client.ts:47-50` throws `response.text()` rather than extracting FastAPI's JSON `detail`. This can show a JSON object instead of a clear corrective message, contrary to BR-021's actionable-error expectation.

13. **One pure budget-validation endpoint is unauthenticated.** `backend/app/routers/budgets.py:9-12` has no `get_current_user` dependency, while the other report operations require authentication. It returns only a calculation and does not access report data, so immediate data-exposure impact is low; it is nevertheless inconsistent with the project's authenticated-API boundary.

14. **Logout is client-side token removal only.** The UI clears local storage and routes to login, and frontend tests cover this. There is no server-side token revocation; a copied bearer token remains usable until its expiry (default 60 minutes). This is a local-demo limitation to account for in production security planning.

### Low — traceability and verification fidelity

15. **ORM contract tests do not prove the live database matches.** `backend/tests/test_model_contract.py:7-79` checks the model metadata's table names, selected composite FKs, delete/update actions, and named indexes. It does not introspect MySQL, compare every column/nullability/type/unique key/default, or inspect triggers. The test named `test_models_match_all_live_table_names` compares only `Base.metadata.tables` to a fixed set.

16. **ORM/SQLite metadata omits the schema's `CHECK` constraints.** `database/schema.sql` defines checks for distinct initiative lineage, cycle date order, budget line number 1–100, and attachment size. `backend/app/models/__init__.py` does not declare those checks. MySQL DDL still defines them when the actual database has this schema, but SQLite `Base.metadata.create_all()` fixtures do not exercise them; tests therefore cannot establish those database-level guarantees.

17. **Guidance has two internal consistency issues.** `.claude/skills/rollover-test/SKILL.md:12` directly refers to RFP page numbers despite the project's rule that the consolidated business-rules file is standalone and the source documents are confidential/unavailable to implementation guidance. Also, `.claude/rules/01-architecture.md:13` says production hosting remains unresolved because source language conflicts, while `ProductionUpdate.md:17` already directs use of a non-Council-hosted environment. Resolve the hosting decision in the production register before treating it as settled. Finally, `BR-019` labels both Council editing/history and historical retention in separate sections of `.claude/rules/02-business-rules.md`, which makes requirement traceability ambiguous.

18. **The backend dependency manifest does not lock the documented Pydantic major version.** `AGENTS.md` specifies Pydantic v2 and the code uses v2 APIs such as `ConfigDict` and `model_dump`, but `requirements.txt` does not declare or constrain Pydantic. FastAPI brings Pydantic transitively, so a fresh resolution commonly selects v2, but the manifest does not guarantee that backend contract across environments.

## Requirement status matrix

Status describes the current code by inspection. “Implemented” does not mean freshly verified against live MySQL; backend runtime verification is blocked as stated above.

| Requirement | Status | Evidence / gap |
| --- | --- | --- |
| BR-001 initiative portfolio | Partial | Relational model supports multiple fiscal-year initiatives; no in-app portfolio administration. |
| BR-002 reporting cycles | Partial | Open-cycle lookup exists; no cycle administration or date-window behavior in the application. |
| BR-003 report content | Partial | JSON forms and budgets exist; form types/layout capabilities are limited. |
| BR-004 common/specific configurable forms | Partial | Templates are read dynamically; no form builder, central question management, conditional logic, or embedded tables. |
| BR-005 organization assignments | Partial | M:N assignments are used and have no fixed 100-org limit; no in-app assignment management. |
| BR-006 separate obligations / duplicates | Implemented | Unique DB key plus server-side duplicate check; assignment tuple is per initiative, organization, cycle. |
| BR-007 / BR-011 individual accounts | Partial | Authentication is per database user; user creation/provisioning is not available in the application. |
| BR-009 EIN eligibility | Partial | Assignment is tied to organization IDs from the EIN registry; no user-facing EIN validation flow. |
| BR-010 organization isolation | Implemented by inspection | External list/detail/save/upload/download paths check organization membership; role checks are backend-side. |
| Organization shared history | Implemented by inspection | Submission list scopes by member organizations, so reports by other members are visible. Snapshot-history presentation is still missing. |
| BR-012 supporting documents | Partial | Multiple local uploads, metadata, 25 MiB cap, authorization and path containment exist; type/content allowlist/validation is missing. |
| BR-013 save and resume | Partial | DB drafts and debounced autosave exist; malformed/incomplete budget amounts can block autosave. |
| BR-014 confirmation / reminders (should) | Partial / Missing | UI confirms and server logs the ID; no submitted snapshot notification or reminder workflow. |
| BR-015 annual rollover | Missing | No rollover API or UI. |
| BR-016 initiative lineage | Partial | Schema/model support lineage; no application management or lineage view. |
| BR-017 Council roles and administration | Partial | Admin/reviewer/view-only role checks exist; only user listing is implemented, no add/manage/reset actions. |
| BR-018 user scale | Partial | No fixed user cap is encoded; no provisioning or pagination, and no live load check. |
| BR-019 Council editing / historical records | Partial | Review/audit and submit snapshots are stored; Council cannot edit submitted reports and snapshots are not viewable in UI. |
| BR-020 data portability | Missing | No bulk data export. Local DB storage itself does not provide a user-facing portability function. |
| BR-021 submission validation | Partial | Server checks required fields and supported data types/limits on submit; no conditional rules and frontend error formatting is weak. |
| BR-022 calculations / configured balance | Implemented by inspection | Decimal backend totals, 100-row cap, configured reconciliation; no universal balance is imposed without a template target. |
| Council oversight, query, triage | Partial | Queue supports basic text/status/balance filters; missing obligations, incomplete/invalid, dynamic data query, and flag controls are absent. |
| Excel / CSV exports | Missing | No implementation found. |
| Submitter PDF print/export | Missing | No implementation; UI documents this limitation. |
| Council charts/visualizations | Missing | No charts or visualization module found. |

## Architecture and database-contract review

- Runtime architecture matches the local-demo boundary: React/Vite, FastAPI/SQLAlchemy, MySQL-configured database access, filesystem uploads at repository-root `.uploads/`, console-only notification logging, and no schema creation at startup (`backend/app/db/__init__.py:init_db`).
- Authentication decodes JWT identity, reloads the user and active state from the database, and uses the database role rather than trusting the token role. External report access is scoped through `user_organizations` and initiative assignments.
- Critical submission composite FKs, restrictive delete rules, snapshot-version FK, and table/index names are represented in the ORM by inspection. The checked-in schema contains audit/version/template triggers; SQLite tests do not run MySQL triggers. A read-only comparison to the current live schema remains necessary before claiming production compatibility.
- The schema and demo seed appear referentially connected by static review. The seed is documented as one-time use against an empty disposable schema; the README's reset example warns that it drops all data. No SQL was run during this audit.
- `.env.example` contains placeholders and the root `.gitignore` excludes `.env*` except `.env.example`, root `.uploads` contents except `.gitkeep`, and confidential source attachments. No secret values were inspected.
- Frontend route guards and backend authorization complement one another. Frontend route checks alone are not relied upon for submission access. Logout is tested as a client-side action.

## Suggested remediation order

1. Restore a functioning Python environment, run compile/tests, then perform a read-only live MySQL metadata comparison and a seeded-account login check against an explicitly local demo DB.
2. Correct the demo seed/README mismatch by ensuring an eligible organization has an unsubmitted open cycle; verify `/api/submissions/available` after seeding.
3. Close core workflow gaps: allow draft persistence during incomplete budget entry; validate upload extensions and actual content; return clear validation messages; expose reviewer snapshots and support authorized Council edits with immutable version/audit records.
4. Add the required application administration/configuration workflows: users/roles/memberships and credential reset, EIN registry validation/autofill, initiative/cycle/assignment/form management, and annual rollover.
5. Add missing oversight and portability features: missing/incomplete obligation triage, richer query/filtering, exports, PDF output, and charts; then complete confirmation/reminder behavior within the local console-notification boundary.
6. Align the rollover skill and production-hosting note with the standalone SSOT and unresolved hosting decision; expand the ORM contract test to compare all available metadata and explicitly label static SQLite checks versus live MySQL verification.
