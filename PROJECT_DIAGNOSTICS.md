# Project Diagnostics

**Review date:** 2026-10-13

**Scope:** Current frontend and backend behavior, tests recorded after the latest implementation changes, seed data, database/ORM mapping, setup instructions, and local-demo boundaries.

## Review basis and limits

This report uses [`.claude/rules/02-business-rules.md`](.claude/rules/02-business-rules.md) as the application-requirements SSOT, along with the applicable project rules and skills. The confidential source attachments were not opened. No `.env` values, uploaded files, database dumps, or real credentials were read. No live MySQL connection or live-schema comparison was performed, so this is not a claim that the connected database matches the ORM or checked-in DDL.

The repository was reviewed after the recent workflow and administration changes. This update changes this diagnostic document only; it does not change application code, seed data, schema, or guidance. Verification results below are from the latest code checks recorded in the preceding implementation turn; only documentation checks are run for this report refresh.

## Executive summary

The application now supports substantially more of the local-demo workflow than the previous report described: database-backed draft persistence and submission, role and organization authorization, review decisions, immutable submission snapshots, audited Council edits, upload/download handling, user-role administration, portfolio configuration, rollover, oversight summaries, CSV/XLSX export paths, and print-to-PDF through the browser.

One user-visible issue remains in the sample setup: every assignment in an open reporting cycle in `database/seed_demo.sql` already has a submission. The availability endpoint correctly hides assignments with an existing submission, so a fresh seeded submitter cannot start a new report even though `README.md` says the seed includes an open unstarted assignment.

Other material gaps are incomplete audit coverage; no account or organization creation flow; no submitter EIN lookup/autofill; a limited JSON-based form builder without conditional logic or embedded tables; incomplete dashboard filters and overdue/validation triage; no scheduled reminders or full-snapshot email; and no unit-cost-times-quantity budget columns. XLSX has an implementation path, but the XLSX test was skipped in the available environment because its optional runtime packages were not installed. Local tests do not prove compatibility with live MySQL.

## Verification status

| Check | Latest recorded result |
| --- | --- |
| `python -m compileall -q backend/app` | **Passed** using the installed Python interpreter and the existing local test environment. The default Windows Python launcher had failed earlier; that earlier failure is superseded by this successful compile check. |
| `python -m pytest backend/tests -q` | **50 passed, 1 skipped** in the latest recorded run, before the XLSX dependencies were installed. The XLSX export test skipped because `pandas` or `openpyxl` was unavailable then. |
| `npm run lint` from `frontend/` | **Passed.** |
| `npm test -- --run` from `frontend/` | **50 passed.** These are frontend tests with mocked API behavior, not end-to-end MySQL/browser tests. |
| `npm run build` from `frontend/` | **Passed.** |
| XLSX export runtime | `pandas 3.0.6` and `openpyxl 3.1.5` are now installed in the ignored `.venv/Lib/site-packages`; imports succeed. The focused API export check has not been rerun, and the backend must use this same environment (or install the requirements into its active environment). |
| Live MySQL metadata comparison and seeded-account login | **Not performed.** The ORM contract suite is static/SQLite-based and the current MySQL configuration was not used. |
| `git diff --check` | **Run after this report edit; result recorded below.** |
| Claude commit hook | **Not run.** No commit was attempted. |

## Findings

### High priority

1. **Seeded submitters have no open unstarted report.** `database/seed_demo.sql` creates three OPEN cycles and assigns organizations to them, but each eligible initiative/organization/cycle tuple has a submission (`database/seed_demo.sql`, organization assignments and submission inserts). `list_available_reports()` intentionally removes tuples that already have a submission (`backend/app/services/submission_service.py:35-93`). The test `test_available_report_can_be_started_from_database_assignment` creates a second open cycle at test time; it does not verify the checked-in seed. `README.md` currently claims there is an open unstarted assignment. **Impact:** a clone seeded exactly as documented shows no available report to start. **Next:** reserve at least one active eligible assignment in an OPEN cycle without a submission, then verify the seeded submitter can see and start it without manually changing data.

2. **Audit coverage is narrower than the business rule.** Submission, reviewer, and Council-edit events create `AuditLog` records (`backend/app/services/submission_service.py:207-248, 345-480, 538-594`; `backend/app/routers/submissions.py:203-236`). Draft autosaves and account/permission changes do not add audit rows (`persist_submission()` and `backend/app/routers/users.py:48-107`); login also has no audit event (`backend/app/routers/auth.py:16-34`). The existing `audit_logs` table requires a `submission_id`, so user-level events cannot be represented cleanly under the current contract. **Impact:** the app cannot demonstrate the full login/autosave/permission-change ledger described by the SSOT. **Constraint:** do not change schema or triggers without explicit authorization; record this as a current contract limitation.

3. **Account and organization lifecycle remains seed/database dependent.** Council admins can list existing users, change role/active state and EIN-based organization memberships, and reset passwords (`backend/app/routers/users.py:19-107`; `frontend/src/routes/UserPage.tsx`). There is no API or UI for creating user accounts or adding/editing the master organization registry. **Impact:** a fresh installation can use the documented demo personas, but administrators cannot onboard a new person or organization entirely in the portal. This leaves account lifecycle and the authoritative EIN registry only partially managed in-app.

4. **Form configuration is versioned but not a complete dynamic form engine.** Admins create versioned templates through a JSON text editor (`backend/app/routers/admin.py:166-219`; `frontend/src/routes/InitiativeAdminPage.tsx`). The submitter renderer handles basic text, narrative, numeric, date, select, and boolean controls (`frontend/src/routes/ReportEditorPage.tsx:276-324`), and the backend validates required/type/length/word-count rules (`backend/app/services/submission_service.py:596-677`). It does not implement conditional/branching questions or embedded calculated tables; the UI flattens fields rather than presenting section-level form structure. **Impact:** configuration and validation are useful for the current seed, but not equivalent to the broader form requirements.

### Medium priority

5. **EIN matching exists for assignment, but submitter lookup/autofill does not.** Assignment creation and membership updates resolve an EIN against an active organization record (`backend/app/routers/admin.py:147-164`; `backend/app/routers/users.py:64-80`). The external portal uses its already-linked organization IDs and does not collect an EIN, show a master-record validation result, or auto-fill organization details. The organization API is list-only. See BR-009 and BR-023/024 status below.

6. **Oversight filters and triage do not cover every requested dimension.** The review queue supports status, unbalanced-only, and a text search over submission ID, initiative name, organization name, and cycle (`backend/app/services/submission_service.py:130-205`; `frontend/src/routes/ReviewPage.tsx`). It does not filter by EIN, borough, fiscal year, or an independent initiative/cycle selector. The open-obligations view lists eligible assignments without a submission, but does not label overdue items or report validation-error details. The queue marks incomplete records, although the flag combines form/budget invalidity and balance state into one boolean. Analytics currently provide status counts, budget totals, and borough totals with simple bars (`backend/app/routers/admin.py:221-267`; `frontend/src/routes/ReviewPage.tsx`), rather than a broader program-progress visualization suite.

7. **Budget arithmetic covers totals, not the requested quantity model.** Backend calculations use `Decimal`, enforce the 100-line boundary, and check configured reconciliation before submission (`backend/app/services/budget_service.py`; `backend/app/services/submission_service.py:345-425, 679-715`). The browser computes display totals using integer cents, and the grid includes category, description, budgeted amount, and actual amount (`frontend/src/routes/ReportEditorPage.tsx:334-367`). The existing `budget_line_items` schema has no unit-cost or quantity columns, so unit cost × quantity row subtotals cannot be captured without changing the database contract. **Status:** total and reconciliation behavior is implemented; the full spreadsheet calculation model is partial.

8. **PDF output is browser print, not a dedicated grid-accurate export.** The report workspace provides `window.print()` / browser “Save as PDF” (`frontend/src/routes/ReportEditorPage.tsx:400-415`). This is useful for a local demonstration but is not a separately generated, tested PDF export with a stable report layout.

9. **Confirmation and reminder communications are incomplete.** The UI shows a submission receipt, and the backend logs confirmation metadata (submission ID, actor, total, and line count) without logging report content (`backend/app/routers/submissions.py:268-309`). No full form/budget snapshot is dispatched by email. No reminder schedule, recipient configuration, or reminder workflow exists. Console logging is an intentional local-demo transport boundary; it does not satisfy the full email/reminder behavior.

10. **Upload checks validate declared metadata, not file signatures.** Uploads enforce the 25 MiB cap, an extension/MIME allowlist, safe generated storage names, repository-root `.uploads/` containment, checksum metadata, and attachment access checks (`backend/app/services/upload_service.py:10-100`; `backend/app/routers/submissions.py:238-265, 312-349`). MIME type is supplied by the client and content bytes are not inspected to confirm the declared file format. Malware scanning is production work listed in `ProductionUpdate.md`; it is not present in the local demo.

11. **Logout and direct-route access work in the local browser, with stateless-token limits.** `RoleRoute` protects portal routes and renders access denied for the wrong role (`frontend/src/App.tsx:19-48`); `/user_page` is admin-only and `/api/admin/users` is independently role-protected. The logout handler clears the stored token and routes to `/login` (`frontend/src/components/Layout.tsx`; `frontend/src/hooks/useAuth.ts`). Frontend tests exercise role denial and logout (`frontend/src/App.test.tsx:73-86, 116-186, 299-318`). There is no server-side token revocation; a copied JWT remains usable until expiry. This is a local-demo limitation, not a finding that the visible logout button is currently broken.

12. **XLSX export has not yet been verified after installing its dependencies.** `/api/admin/exports/xlsx` builds workbook sheets using `pandas` and `openpyxl` (`backend/app/routers/admin.py:323-338`); both are in `requirements.txt` and are now importable from the ignored `.venv/Lib/site-packages`. The latest backend run skipped the focused export test before installation, so rerun that test in the backend's active environment before relying on the route.

### Lower priority: project-contract and documentation mismatches

13. **The checked-out `AGENTS.md` links to absent context documents.** It instructs agents to read `context/rfp-functional-specs.md` and `context/db-schema-reference.md`, but there is no `context/` directory in the current checkout. The business-rules and database-contract rules are present under `.claude/rules/`; `database/schema.sql` is also present. Clarify the intended repository setup artifacts while keeping the live schema authoritative; do not infer live compatibility from the checked-in file.

14. **The confidential-source/standalone-SSOT policy is not reflected consistently in guidance.** `.claude/rules/02-business-rules.md` says it consolidates named source documents and retains `[cite: ...]` markers. `.claude/skills/rollover-test/SKILL.md` refers directly to RFP page numbers, and `.claude/skills/budget-validate/SKILL.md` refers to the RFP. These instructions conflict with the user's earlier requirement that source business documents remain confidential and unavailable from application/agent instructions. This diagnostics report used only the consolidated SSOT and does not reproduce those sources.

15. **Production-hosting wording is inconsistent across project guidance.** `ProductionUpdate.md` directs selection of an approved non-Council-hosted production environment, while `.claude/rules/01-architecture.md` says hosting language is conflicting and remains a decision to resolve. The local demo correctly defers hosting, compliance, incident response, support, mail delivery, resilience, and capacity commitments; align the production guidance before treating the hosting choice as settled.

16. **ORM contract tests are not live-schema verification, and ORM checks are incomplete.** `backend/tests/test_model_contract.py` compares declared SQLAlchemy metadata to a hard-coded contract; it does not introspect a live MySQL schema or compare triggers. The ORM models do not declare the DDL `CHECK` constraints for distinct lineage IDs, cycle date order, line number 1–100, or attachment size (`database/schema.sql:42, 56, 139, 173`; `backend/app/models/__init__.py`). SQLite fixtures therefore do not exercise those MySQL constraints/triggers. This is a coverage limitation, not authorization to modify schema.

17. **The backend dependency manifest does not explicitly constrain Pydantic v2.** `requirements.txt` constrains FastAPI but has no direct Pydantic requirement, while schemas use Pydantic v2 features. A clean dependency resolution should explicitly guarantee the version expected by the code.

## Business-rule status matrix

“Implemented” means supported by the checked-in application and/or focused tests; it does not certify live MySQL behavior. “Not applicable to the local demo” is limited to legal, vendor, hosting, or production operations that this local application cannot demonstrate.

| Rule | Status | Evidence and current limit |
| --- | --- | --- |
| BR-001 Initiative portfolio | **Partial** | Admin can create, rename, and change lifecycle status; rollover clones initiatives. No explicit combine/merge administration and no ~175-initiative load test (`admin.py:90-117, 348-382`). |
| BR-002 Reporting cycles | **Partial** | Admin can create cycles, dates, and status; no requirement that every initiative has at least two cycles/year or automatic date-driven opening/closing (`admin.py:118-145`). |
| BR-003 Report content | **Partial** | Configurable metrics/narratives and budget rows exist; conditional fields and embedded calculated tables do not (`ReportEditorPage.tsx`; `submission_service.py:596-677`). |
| BR-004 Common and initiative-specific forms | **Partial** | Versioned initiative templates and JSON editor exist; no shared/common template composition, visual schema editor, conditional logic, or embedded tables (`admin.py:166-219`; `InitiativeAdminPage.tsx`). |
| BR-005 Organization assignments | **Partial** | Admin can assign an active registry organization by EIN; no >100-organization scale test (`admin.py:147-164`). |
| BR-006 Separate obligations and duplicate prevention | **Implemented** | One submission per initiative/organization/cycle is enforced by service checks and the unique DB key; eligible reports are derived from assignments and open cycles (`submission_service.py:35-93, 250-323`; model contract test). |
| BR-007 Multiple submitters per organization | **Partial** | Individual user identities and many-to-many memberships exist; no user-creation workflow, and one shared obligation row prevents separate parallel submissions for the same org/initiative/cycle (`users.py`; `uq_sub_instance` model/schema). |
| BR-008 100-line financial grid | **Partial** | 1–100 lines, descriptions, budgeted/actual amounts, totals and variance exist; unit-cost × quantity row calculations are absent from the schema and UI (`budget_service.py`; `ReportEditorPage.tsx:334-367`). |
| BR-009 EIN-based eligibility | **Implemented** | Backend derives an external user's organization IDs from memberships and requires an active assignment for the initiative/cycle before report creation (`dependencies.py`; `submission_service.py:250-323`). |
| BR-010 Organization isolation | **Implemented** | Backend access checks use current DB identity and memberships for submission operations and attachment access; role/organization tests are present (`dependencies.py`; `submissions.py`; `test_auth.py`, `test_submission_uploads.py`). |
| BR-011 Account-based identity | **Partial** | Authentication is individual and password-hashed; admins can update existing accounts, but cannot create new accounts in the portal (`auth.py`; `users.py`). |
| BR-012 Supporting documents | **Partial** | Multi-file uploads, 25 MiB cap, metadata/checksum, allowlist, path safety, and access controls exist; content signatures are not verified (`upload_service.py`; `submissions.py`). |
| BR-013 Save and resume | **Implemented** | Drafts persist to MySQL, incomplete budget text is retained for later editing, autosave is debounced, and submission validation remains strict (`submission_service.py:345-535`; `ReportEditorPage.tsx:176-232`). |
| BR-014 Confirmation email | **Partial** | Receipt UI and safe confirmation metadata logging exist; no email with the complete report snapshot (`submissions.py:268-309`; README local-demo boundary). |
| BR-015 Annual rollover | **Partial** | Admin rollover copies active initiatives, cycles, assignments, and template versions while preserving source data; it does not provide shared-form composition or an idempotent/recovery policy (`admin.py:348-382`; rollover test). |
| BR-016 Historical lineage | **Partial** | Rollover creates predecessor/successor `RENAMED` links and the admin UI displays lineage; no in-app combine/split relationship workflow (`admin.py:348-382`; `InitiativeAdminPage.tsx`). |
| BR-017 Council administration | **Partial** | Existing users' role/active state/memberships and passwords are managed; no account creation, and population scale is not load-tested (`users.py`; `UserPage.tsx`). |
| BR-018 External-user scalability | **Partial** | Relational user/membership model has no fixed account cap; no performance/capacity test establishes indefinite scale (`models/__init__.py`; tests). |
| BR-019 Perpetual retention and history | **Partial** | Submission versions and audit rows are retained/immutable by schema triggers; history is visible. Login, draft-autosave, and permission-change events are not recorded; no operational retention proof (`submissions.py:112-201`; `submission_service.py`; schema triggers). |
| BR-019A Council edit and review history | **Implemented** | Review transitions, revision requests, admin edits, new immutable snapshots, and audit notes are implemented and covered by focused tests (`submission_service.py:207-248, 538-594`; `ReviewDetailPage.tsx`; tests). |
| BR-020 Council data ownership | **Not applicable to the local demo** | Ownership is a legal/contractual property of the deployment; this local code review cannot establish it. No third-party production hosting was tested. |
| BR-021 Pre-submission validation | **Partial** | Server validates required fields, supported types, word/length bounds, budget rows, and configured reconciliation; no conditional rules and no field-by-field inline error mapping (`submission_service.py:345-425, 596-677`; editor). |
| BR-022 Hard financial balancing | **Partial** | Server uses `Decimal` and enforces a configured target when present; current row model lacks unit cost/quantity math, and templates without a target are not forced to an arbitrary balance (`budget_service.py`; `submission_service.py:679-715`). |
| BR-023 EIN master validation | **Partial** | Admin assignment and membership updates validate EIN against active registry rows; portal cannot create/maintain the master registry or perform a submitter-facing EIN check (`admin.py:147-164`; `users.py:64-80`). |
| BR-024 Organization detail autofill | **Missing** | No submitter EIN entry/lookup flow or autofill of organization details was found. |
| BR-025 Breach notification and remediation | **Not applicable to the local demo** | Incident response and Council/vendor notification are operational commitments, not implemented or verified in this local stack. |
| BR-026 Hosting/compliance boundary | **Not applicable to the local demo** | The app uses local MySQL and filesystem uploads; no production hosting boundary or FedRAMP/NIST controls are demonstrated. Project wording needs alignment (finding 15). |
| BR-027 Production go-live target | **Not applicable to the local demo** | A production milestone is not established by local application behavior. |
| BR-028 Annual review and lifecycle maintenance | **Partial** | Admin can change initiatives, cycles, assignments, and form versions and can run rollover; no annual review workflow/checklist is implemented. |
| BR-029 Testing, training, and support SLA | **Not applicable to the local demo** | Vendor support commitments cannot be verified in this application. |

### Business-rule requirements without their own numbered row

| Capability | Status | Evidence and current limit |
| --- | --- | --- |
| Council oversight dashboard | **Partial** | Queue, status summary, budget summary, and borough totals exist; filters do not cover all requested fields. |
| Incomplete, unbalanced, missing, overdue, and validation-error triage | **Partial** | Unbalanced/incomplete flags and open unstarted obligations are visible; overdue classification and detailed validation-error triage are absent. |
| CSV and Excel exports | **Partial** | CSV ZIP bundle is implemented; XLSX workbook is implemented but its test was skipped in this environment due unavailable runtime packages. |
| Grid-accurate PDF | **Partial** | Browser print/save-as-PDF is available; no dedicated export implementation verifies layout fidelity. |
| Visualizations | **Partial** | Status and borough budget summaries use bar-style displays; broader progress and spend analytics are absent. |
| Automated reminders | **Missing** | No reminder scheduler, recipient configuration, or reminder dispatch path exists. |

## Security, persistence, and architecture review

- **Authentication and roles:** Login verifies the password hash; each protected backend request resolves the current user from the database, and routes enforce role permissions. Frontend route guards provide user-facing access-denied behavior but are not the only security layer (`backend/app/core/dependencies.py`; `frontend/src/App.tsx`).
- **Organization scope:** Submitter listing, create, read, write, upload, and download operations are checked against linked organization IDs. Council review roles and `VIEW_ONLY` use separate access paths. Focused SQLite tests cover representative cross-role and cross-organization cases; live MySQL is unverified.
- **Persistence and history:** Submissions and budget rows persist in MySQL; final submissions and Council edits create version snapshots. Review and submit actions create audit records. The existing schema's triggers protect immutable versions/audit rows and published template definitions, but SQLite tests do not execute those MySQL triggers.
- **Budget safety:** Monetary backend work is `Decimal`-based; client-supplied totals are not trusted for final reconciliation. Draft entry can persist incomplete values; final submission validates the configured target and row boundaries.
- **Uploads:** Files are stored under repository-root `.uploads/`, with metadata in MySQL. `.gitignore` excludes upload content and `.env` while keeping `.env.example`; no uploaded sample documents are committed.
- **Database contract:** `database/schema.sql` exists as a setup artifact and `database/seed_demo.sql` is intended for an empty disposable local database. No schema, trigger, or seed SQL was executed for this review. The checked-in DDL is not evidence of the current live schema.
- **Local-demo boundaries:** Console confirmation logging, in-process behavior, local MySQL, and filesystem storage match the stated demo architecture. Email transport, scheduled reminders, production security/compliance, support operations, backup/recovery, and production capacity remain outside the verified local boundary.

## Recommended remediation order

1. Fix the synthetic seed/README mismatch so a clean clone has one eligible, open, unstarted report; test the seeded dashboard and report-start flow.
2. Define how to record login, draft-save, and permission changes without weakening the live schema. Keep schema changes out of scope until explicitly authorized.
3. Complete the master organization and account lifecycle, including user provisioning and submitter EIN lookup/autofill, if those actions must be performed entirely in the portal.
4. Extend form configuration/rendering for section-aware forms, conditional logic, shared questions, and embedded/calculated tables while preserving published template versions.
5. Add filter dimensions, overdue classification, and actionable validation-error detail to the Council queue; broaden analytics based on the actual requirements.
6. Decide whether the current budget schema can meet unit-cost/quantity requirements. Do not alter the live schema implicitly; capture any required schema decision before implementation.
7. Verify XLSX export in an environment with `requirements.txt` installed. Assess PDF fidelity and implement the required confirmation/reminder behavior within the approved local-demo boundary.
8. Resolve the missing `context/` references, confidential-source references in guidance, hosting wording mismatch, and explicit Pydantic v2 dependency. Perform a read-only live MySQL-to-ORM comparison before claiming database compatibility.
