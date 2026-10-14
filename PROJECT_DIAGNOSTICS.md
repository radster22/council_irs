# Project Diagnostics

- **Review date:** 2026-10-14 (second pass)
- **Commit / Checkpoint:** Based on `578858446fea6cf5880bdd78f3eab16ef97390c3`; the changes in Section 4 are committed on branch `fix/upload-errors-ein-registry`. Unrelated working-tree edits (`AGENTS.md` removal, new `CLAUDE.md`, `ProductionUpdate.md`, `database/schema.sql`) are not part of that commit and were not audited here.
- **Scope:** Active local demo requirements, file upload validation and error UX, EIN registry validation/autofill, budget grid editing, review/revision workflow, exports, print layout, and verification suite.

---

## 1. Review Basis and Limits

This audit evaluates the codebase against [`.claude/rules/02-business-rules.md`](.claude/rules/02-business-rules.md) and `CLAUDE.md` / `AGENTS.md`.
- Evaluated strictly within the local host boundary: local MySQL 8.0, filesystem storage at repository-root `.uploads/`, and console-logged notifications.
- Database DDL in `database/schema.sql` is treated as a frozen contract. No schema change was made; the registry import writes only existing `organizations` columns.
- **Live MySQL was not checked in this review.** Backend results come from the SQLite-backed test suite, which cannot prove MySQL JSON/ENUM/trigger compatibility.

---

## 2. Executive Summary

The project is functionally ready for the primary local demonstration path. All previously listed medium-priority issues are resolved:
- **Authentication & Personas**: Pre-seeded logins with bcrypt-hashed credentials and role enforcement (`COUNCIL_ADMIN`, `COUNCIL_REVIEWER`, `VIEW_ONLY`, `EXTERNAL_SUBMITTER`).
- **External Submitter Portal**: Organization-scoped isolation, draft autosave, 100-line budget grid, balance enforcement on submit, revision-request banner, and an inline correction message when a selected file exceeds 25 MB.
- **EIN Registry**: Council admins can import the authoritative organization list (CSV, all-or-nothing validation). The assignment form validates each EIN against the registry as it is typed and autofills the organization's details.
- **Council Finance Review**: Review queue with multi-field filters, triage, review actions, audited admin edits, and versioned snapshots.
- **Portability & Lifecycle**: Fiscal-year rollover with lineage, `.xlsx` workbook export, and CSV bundle export.

---

## 3. Verification Summary (2026-10-14, second pass)

| Check | Result | Notes |
| :--- | :--- | :--- |
| `python -m compileall -q backend/app` | **Passed** | No compile errors. |
| `python -m pytest backend/tests -q` | **Passed** | 64 passed, 0 skipped, 1 warning (Open Issue 1). Includes 5 new EIN registry tests. |
| `npm run lint` from `frontend/` | **Passed** | `tsc --noEmit` reported zero errors. |
| `npm test -- --run` from `frontend/` | **Passed** | 56 passed across 3 files, including 4 new `ReportEditorPage.test.tsx` tests. The focus test was confirmed to fail against the old `${index}-${line.category}` key. |
| `npm run build` from `frontend/` | **Passed** | Vite production build succeeded. |
| `git diff --check` | **Passed after this update** | The previous diagnostics file had trailing-space Markdown line breaks, which would have failed the pre-commit hook. This version removes them. |
| Live MySQL Introspection | **Not run** | No live connection was attempted. |
| Manual browser check | **Not run** | UI behavior is verified by component tests, type-check, and build only. |

---

## 4. Issues Resolved in This Pass

| # | Issue | Fix | Verification |
| :--- | :--- | :--- | :--- |
| 1 | **Oversized upload showed no visible correction message.** The size error was set on the shared editor error banner, which renders at the bottom of Step 4, far from the upload control. | `ReportEditorPage.tsx` checks file size when files are selected. An oversized file clears the picker, disables Upload, and shows "*name* is larger than 25 MB. Upload a file smaller than 25 MB." in an `role="alert"` box directly under the upload control. Upload failures from the backend (type mismatch, 413) also appear there. | `ReportEditorPage.test.tsx`: rejects 25 MiB + 1 byte with no API call; accepts exactly 25 MiB; backend upload error shows inline. |
| 2 | **BR-024: EIN autofill not implemented.** | New `GET /api/admin/organizations/lookup?ein=` (admin only) returns registry details for a hyphenated or digits-only EIN. In `InitiativeAdminPage.tsx`, the assignment form checks each typed EIN against the registry (300 ms debounce), then fills in legal name, EIN, type and borough. Until an active registry match is found, the Assign button stays disabled and the reason is shown. | Backend test covers both EIN formats, 404 for unknown, 422 for malformed, and 403 for submitters. |
| 3 | **BR-023: EIN master validation was partial.** | New `backend/app/services/organization_service.py` holds EIN normalization, registry lookup, and `import_organization_registry`. `POST /api/admin/organizations/import` (admin only, CSV up to 5 MB) validates every row (EIN format, required legal name, type/status values, field lengths, duplicate EINs). One bad row rejects the whole file with row-numbered errors. Otherwise it creates new organizations, updates changed details, and lists active organizations missing from the file without deleting or deactivating them. The panel is on `UserPage.tsx`. | Backend tests cover create/update/report summary and rejecting a whole file for one invalid row. |
| 4 | **EIN format mismatch in assignment.** `create_assignment` compared the raw string, so `456789012` did not match a stored `45-6789012`. Manual organization creation could also duplicate an EIN stored in the other format. | Both now use `find_organization_by_ein`, which accepts either format. A duplicate creation returns 409. | Two backend tests. |
| 5 | **No editor UI test coverage.** | Added `frontend/src/routes/ReportEditorPage.test.tsx` covering Category focus retention, the latest revision comment banner, and upload size handling. | 4 tests pass. |

Resolved in the first pass on 2026-10-14 (retained for history): budget row key focus bug, JSON error-detail parsing, revision comment banner, client-side 25 MB pre-check, CSV binary-content test, XLSX test no longer skipped, and print table borders.

---

## 5. Open Issues

### Low Priority
1. **Deprecated status constant**: `backend/app/routers/submissions.py:347` uses `HTTP_413_REQUEST_ENTITY_TOO_LARGE`, which emits a `DeprecationWarning` under the installed Starlette 0.48. It is kept on purpose because older Starlette versions allowed by `fastapi>=0.115` lack the replacement name.
2. **BR-014 / reminders**: The business rules specify confirmation and reminder emails. The demo prints confirmations to the console, which matches the local boundary in `01-architecture.md`. Production email belongs in `ProductionUpdate.md`.
3. **Registry import is not audit-logged**: `audit_logs` is tied to submission events in the existing schema. Organization registry changes are returned in the import summary but are not written to an audit table, and recording them would need a schema decision.
4. **Pre-commit hook scope**: Some multi-line Bash heredoc commands (not `git commit`) triggered `.claude/hooks/pre-commit-checks.mjs` through the `if: "Bash(git commit *)"` filter and were blocked. This affects only agent tooling, not the application.

---

## 6. Requirement Status Matrix (Active Demo Scope)

| Rule ID | Rule Name | Demo Status | Implementation Evidence |
| :--- | :--- | :--- | :--- |
| **BR-001** | Initiative Portfolio | **Implemented** | CRUD via `/api/admin/initiatives` and `InitiativeAdminPage.tsx`. |
| **BR-002** | Reporting Cycles | **Implemented** | Cycle creation via `/api/admin/initiatives/{id}/cycles`. |
| **BR-003** | Comprehensive Content | **Implemented** | Dynamic JSON programmatic answers + budget grid. |
| **BR-004** | Form Management | **Implemented** | Versioned form templates via JSON schema editor. |
| **BR-005** | Organization Assignments | **Implemented** | Assignments via `/api/admin/initiatives/{id}/assignments`, accepting either EIN format. |
| **BR-006** | Separate Obligations | **Implemented** | Unique constraint `(initiative_id, organization_id, cycle_id)`. |
| **BR-007** | Multiple Submitters | **Implemented** | Multiple accounts linked via `user_organizations`. |
| **BR-008** | 100-Line Financial Grid | **Implemented** | 1–100 row grid with totals and variance; Category focus covered by a component test. |
| **BR-009** | EIN-Based Eligibility | **Implemented** | Submissions restricted to assigned initiative/cycle tuples. |
| **BR-010** | Access Isolation | **Implemented** | Backend organization-membership checks on all data access. |
| **BR-011** | Account-Based Identity | **Implemented** | JWT authentication with bcrypt password verification. |
| **BR-012** | Supporting Documents | **Implemented** | 25 MiB cap enforced at file selection with an inline correction message, and authoritatively on the backend; type allowlist, signature checks, and CSV binary rejection. |
| **BR-013** | Save and Resume | **Implemented** | Draft autosave and persistence in `ReportEditorPage.tsx`. |
| **BR-014** | Submission Confirmation | **Implemented (Demo)** | Receipt UI plus console log; email delivery is production-only. |
| **BR-015** | Annual Rollover | **Implemented** | `POST /api/admin/rollover` and `RolloverPage.tsx`. |
| **BR-016** | Predecessor Lineage | **Implemented** | Rollover writes `RENAMED` lineage into `initiative_relationships`. |
| **BR-017** | Council Administration | **Implemented** | Role changes, password resets, and user list via `UserPage.tsx`. |
| **BR-018** | External User Scalability | **Implemented (Design)** | No application cap on submitter accounts; capacity not load-tested. |
| **BR-019** | Perpetual Retention | **Implemented** | Snapshots and audit logs protected by immutability triggers (live triggers not rechecked). |
| **BR-019A** | Council Edits & Reviews | **Implemented** | Review actions, audited admin edits, and revision comment shown to the submitter. |
| **BR-020** | Council Data Ownership | **Implemented (Demo)** | Full XLSX/CSV export for portability. |
| **BR-021** | Pre-Submission Validation | **Implemented** | Required fields and balance checks on submit; errors shown as clean messages. |
| **BR-022** | Hard Financial Balancing | **Implemented** | Server-side Decimal enforcement of the configured total. |
| **BR-023** | EIN Master Validation | **Implemented** | Registry CSV import with all-or-nothing row validation; EIN validated against the registry on lookup, assignment, and organization creation. |
| **BR-024** | Organization Autofill | **Implemented** | Registry lookup autofills organization details in the assignment form. |
| **BR-025 / 026 / 027 / 029** | Breach, hosting, go-live, SLA | **Out of Demo Scope** | Production/contractual items; track in `ProductionUpdate.md`. |
| **BR-028** | Annual Review Maintenance | **Supported** | Supported through admin configuration, registry import, and rollover. No dedicated feature. |

---
