# Business Rules Compliance Diagnostic

**Assessment date:** October 11, 2026  
**Snapshot:** Preceded the first assignment-backed reporting workflow increment; statuses below describe the code at that baseline.  
**Scope:** Repository frontend and backend compared with BR-001 through BR-029 in the supplied Business Rules worksheet. The workbook supplies cited RFP page references. The ECI architecture document was used as proposed-design context. The live-schema reference and source code were inspected.

## Executive Summary

The application does **not** currently implement all documented business rules. The frontend and backend are an early local-demo skeleton. Authentication checks a database user, budget validation uses Python `Decimal`, and the schema models several relevant relationships and historical records. However, the central reporting workflow is not persisted: save requests return validated request data without writing submissions or budget lines. Initiative and review screens show hard-coded examples. There is no functioning assignment, configurable form, review, rollover, export, notification, or retention workflow.

The highest-risk gaps are:

1. **Submission and upload authorization do not enforce submission ownership or initiative/organization assignment.** Authenticated users can submit arbitrary route identifiers; the authorization helper exists but is not used by these routers.
2. **Upload path traversal is possible through the route's `submission_id`.** The upload service joins that value directly into a filesystem path. It also reads the entire upload into memory before checking the 25 MiB limit.
3. **Submission is not a real save or submit.** No submission, budget line, version, audit record, or attachment metadata is written to the database.
4. **Configured validation is absent.** The budget check only requires a positive total; it does not evaluate configured required fields or reconcile against an allocated/configured amount. Non-finite Decimal values are not explicitly rejected.
5. **The default JWT signing key is predictable.** `backend/app/core/config.py` uses a committed development fallback if `SECRET_KEY` is unset, and no environment guard prevents it being used outside a local demo.
6. **The frontend has no test script, and backend validation could not run in this environment.** Frontend lint/build pass; backend Python launch fails before compile or tests start.

## Classification Key

- **Implemented:** observable code behavior satisfies the rule within the stated local-demo boundary.
- **Partial:** relevant model, helper, or limited behavior exists, but the end-to-end rule is not met.
- **Missing:** required behavior has no effective implementation.
- **Not applicable (local demo):** a production/contract/operational obligation outside the approved local-demo runtime; this is not a claim of production compliance.

## Rule-by-Rule Assessment

| Rule | Status | Evidence and assessment |
|---|---|---|
| BR-001 Portfolio can change annually; approximately 175 initiatives (RFP p. 6) | Partial | `Initiative` is modeled, but no initiative API or administration exists and the dashboard uses three hard-coded examples. See `backend/app/models/__init__.py`, `frontend/src/routes/DashboardPage.tsx`. |
| BR-002 At least two report collections per initiative per year (p. 6) | Partial | `ReportingCycle` is modeled, but no cycle-management or obligation workflow exists; UI shows a fixed “2026 Q1”. See model and `frontend/src/routes/ReportEditorPage.tsx`. |
| BR-003 Reports combine performance, financial, and narrative information (pp. 6–7) | Partial | `form_data` is generic JSON and budget lines are separately validated, but there is no configured form or persistence. See `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`. |
| BR-004 Common and initiative-specific questions (p. 6) | Missing | `FormTemplate` exists in the model, but there is no schema-driven renderer, template API, or question composition. The report page contains fixed demo fields. |
| BR-005 At least one and potentially over 100 organizations per initiative (p. 6) | Partial | The many-to-many `InitiativeOrganization` model supports assignment cardinality; no assignment administration, data-backed reporting, or scale verification exists. |
| BR-006 Separate report per assigned initiative for organizations with multiple initiatives (p. 6) | Missing | The database has a uniqueness constraint for initiative/organization/cycle, but save does not access or write it and the UI uses a single demo report. |
| BR-007 Different individuals in an organization may submit (p. 6) | Partial | Individual users and `UserOrganization` memberships are modeled; current submit/upload actions do not verify membership in the submission's organization. |
| BR-008 Financial grid supports up to 100 lines (p. 7) | Partial | Backend validation rejects more than 100 lines with `Decimal` arithmetic. The UI permits adding unlimited rows, and the check does not implement configured balancing. See `backend/app/services/budget_service.py`, `frontend/src/routes/ReportEditorPage.tsx`. |
| BR-009 EIN identifies reports an organization must submit (p. 8) | Missing | EIN is stored on `Organization`, but no EIN lookup, master-list validation, or report eligibility logic exists. |
| BR-010 Organizations can access only reports assigned to them (p. 8) | Missing; high risk | `require_organization_access` is defined but not used by submission or attachment routes. Those routes accept any identifier from any authenticated account. See `backend/app/core/dependencies.py`, `backend/app/routers/submissions.py`. |
| BR-011 Individual account-based login (p. 11) | Partial | Login checks an active database account and password. Broader authorization is incomplete; the frontend stores bearer tokens in `localStorage`. See `backend/app/routers/auth.py`, `frontend/src/hooks/useAuth.ts`. |
| BR-012 25 MB maximum per file (pp. 8, 11) | Partial | Service constant enforces 25 MiB after `upload.read()` loads the full file; this creates memory-exhaustion exposure. The route does not validate the submission scope or persist attachment metadata. See `backend/app/services/upload_service.py`, `backend/app/routers/submissions.py`. |
| BR-013 Pause, save, and return later (pp. 8–9, 11) | Missing | Save returns echoed request values and writes nothing. Reloading cannot resume a saved draft. See `backend/app/routers/submissions.py`. |
| BR-014 Email confirmation containing submitted information (pp. 8, 11–12) | Missing | No notification is triggered after submit. Console logging is the local-demo notification choice, but no console notification exists in this flow. |
| BR-015 Carry forms, questions, and layouts into next fiscal year (pp. 9–10) | Missing | No rollover operation exists. Template and initiative models alone do not implement copying or validation of rollover outcomes. |
| BR-016 Link renamed/combined initiatives to predecessors (p. 10) | Partial | `InitiativeRelationship` models `RENAMED`/`COMBINED` links, but there is no administration or historical continuity query/UI. |
| BR-017 Support 50–100 internal users with varied permissions (p. 10) | Partial | Four role values and role-check helpers exist; there is no user administration, permission variation beyond role, or capacity evidence. |
| BR-018 Support an indefinite number of external users (p. 10) | Not applicable (local demo) | No scale test or production capacity evidence exists. The demo has no imposed account cap, but this does not establish the production scalability requirement. |
| BR-019 Retain submitted data in perpetuity (p. 10) | Missing | The current save route persists no data. Immutable version/audit tables exist in the schema, but the app does not write them. Production retention, backup, and recovery are also not configured. |
| BR-020 City Council retains data ownership (p. 10) | Not applicable (local demo) | This is a contractual/hosting obligation; the local application has no ownership, portability, or production hosting controls to assess. |
| BR-021 Block completion until all designated required fields comply (pp. 12–13) | Missing | No configured field definitions or required-field validator exists. `form_data` is accepted as arbitrary JSON. |
| BR-022 Configured sum must equal required total before submission (p. 12) | Missing | Budget service only checks that the total is positive. It does not compare against an expected amount or configured balancing rule; `is_balanced` is not persisted or computed for a submission. |
| BR-023 Validate EIN and organization data against Council master list (p. 13) | Missing | No master-list import, lookup, or validation process exists. |
| BR-024 Auto-fill organization details after validation (p. 13) | Missing | No EIN validation or organization lookup UI/API exists. |
| BR-025 Breach notification and remediation reporting (p. 12) | Not applicable (local demo) | No hosted production operations or incident-response process is part of the local demo. This remains a production obligation. |
| BR-026 Production not on Council-owned servers; cloud with stated security compliance (pp. 8, 10) | Not applicable (local demo) | Current project guidance explicitly scopes a local demo. The architecture document's government-cloud proposal is design context; production hosting/compliance remains deferred and unverified. |
| BR-027 Target go-live February 1, 2027 (pp. 5, 9) | Not applicable (local demo) | Schedule/contract delivery obligation, not a runtime behavior. The codebase does not establish delivery readiness. |
| BR-028 Annual review and change work with Council Finance (p. 7) | Not applicable (local demo) | Ongoing vendor service obligation, not an implemented application behavior. |
| BR-029 Post-launch support, preferably within 24 hours (p. 8) | Not applicable (local demo) | Operational support obligation. “Preferably within 24 hours” is a stated preference, not an unconditional software guarantee. |

## Cross-Cutting Findings

### Critical: submission scope and persistence

`POST /api/submissions/{submission_id}/save` authenticates a user, validates the submitted budget, and returns a response object. It does not load a submission, check user role or organization membership, enforce initiative assignment, or write to SQLAlchemy. The attachment endpoint likewise accepts an arbitrary submission ID and saves a file without checking that the submission exists or belongs to an organization the user may access. The frontend sends placeholder organization/initiative names and a demo ID. This means the interface currently simulates success rather than completing a reporting workflow.

### High: upload path and resource handling

`save_uploaded_file` constructs `UPLOAD_ROOT / submission_id` directly. A path traversal value can escape the upload root. It reads the entire file into memory before checking the configured maximum, so the size check does not prevent large request memory consumption. The endpoint also trusts the multipart filename/content type beyond basename filtering and returns a stored path. No download authorization or attachment metadata persistence is present.

### High: budget and form validation

Currency arithmetic on the backend uses `Decimal`, and the 100-line limit is enforced. However, client preview uses JavaScript `Number`/`parseFloat`; the backend does not explicitly reject `NaN`/infinity or amounts with excess currency precision. More materially, no configured required fields or expected totals are evaluated. The current positive-total rule is not a substitute for the RFP's configurable reconciliation requirement.

### High: JWT configuration can silently use a known key

`backend/app/core/config.py` supplies a hard-coded development signing key when `SECRET_KEY` is absent. Because `APP_ENV` does not guard this fallback, an incorrectly configured deployment could mint or accept forged bearer tokens. Require an explicitly supplied strong secret outside local development and avoid a known fallback for any environment that can hold real data.

### High: workflow, history, and review

There is no database-backed state transition, submission version creation, audit log append, review disposition, revision request, or resubmission flow. The review queue is hard-coded. The schema contains relevant immutable history and audit structures, but their existence is not application behavior.

### Medium: frontend is a prototype

The dashboard and review queue use hard-coded data; the editor uses prefilled static budget lines and labels. `ProtectedRoute` checks only whether a token/user exists in browser state; it does not apply role-based UI restrictions. Server-side enforcement remains required regardless of this UI behavior.

### Verification and environment

- `frontend`: `npm run lint` passed (`tsc --noEmit`).
- `frontend`: `npm run build` passed (TypeScript build and Vite production build).
- `frontend`: `npm test` could not run because `package.json` has no `test` script.
- Backend compile and tests were attempted through `.venv\Scripts\python.exe`; both failed before Python started because the configured base Python executable reported “A specified logon session does not exist.” These are **unverified**, not passing.
- `git diff --check` could not be used because this workspace has no accessible `.git` repository (`git` reports “not a git repository”).
- This host had no command-line PDF text extractor available. Rule assessment used the workbook's RFP citations and extracted rule summaries, plus the architecture DOCX; the PDF wording/page citations were not independently re-parsed in this run. Resolve interpretive conflicts against the RFP PDF before encoding policy.
- No live MySQL query was run during this diagnostic. This report relies on the existing `context/db-schema-reference.md` verification record and does not claim a fresh database verification.

## Recommended Remediation Order

1. **Contain security risks:** require a strong configured JWT key outside local development; validate submission IDs as canonical identifiers; resolve and verify upload paths remain within `.uploads`; stream uploads with a hard byte cap; enforce report existence, role, organization membership, and initiative assignment for save/upload/read/download operations; avoid exposing filesystem paths.
2. **Implement database-backed draft/submission flow:** load or create only valid assigned report instances; persist form data and budget rows; derive user, organization, initiative, cycle, template version, totals, status, and permissions on the server; keep the live schema unchanged.
3. **Implement authoritative dynamic validation:** validate against the selected published template, required fields, conditional rules, data types, line count, and configured reconciliation. Explicitly reject non-finite and invalid precision amounts. Use backend results for displayed financial totals.
4. **Add immutable history and review transitions:** create submission version snapshots and append audit events; implement review, approval/rejection/update-request transitions and organization resubmission without modifying immutable rows.
5. **Build real assigned dashboards/forms and reference data:** replace hard-coded initiative/report/review examples with APIs, add EIN master-list validation/autofill, assignment-driven obligations, and common/initiative-specific forms.
6. **Implement rollover, reporting, and confirmations:** clone/validate annual configurations while preserving lineage; add report confirmation using the local console-notification adapter; implement required exports/dashboards appropriate to the approved demo scope.
7. **Keep production obligations explicitly deferred:** track cloud authorization, retention/backup/recovery, breach response, scale/availability, formal training/testing, annual maintenance, and vendor support in `ProductionUpdate.md`; do not build production infrastructure without approval.
8. **Restore verifiable checks:** repair the local Python runtime, rerun `python -m compileall -q backend/app` and `python -m pytest backend/tests -q`, add a frontend test script and business-rule-focused UI tests, then run the project hook workflow. Preserve schema-contract, upload-security, authorization, and immutable-history regression coverage.
