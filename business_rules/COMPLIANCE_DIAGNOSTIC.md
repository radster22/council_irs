# Business Rules Compliance Diagnostic

**Assessment date:** October 12, 2026

**Scope:** Current repository behavior against BR-001 through BR-029 in the business-rules workbook, using the RFP as the contractual source and the architecture document as proposed design context.
**Evidence basis:** Current source and tests. This is a local-demo assessment, not a production certification or a fresh live-MySQL inspection.

## Summary

The current application implements a database-backed submitter workflow and a Council review workflow. A submitter can see reports for linked organizations, start an eligible report, save/resume a draft, upload supporting files, and submit after server-side form and configured budget validation. Council reviewers and administrators can search/filter submissions, inspect report history, and apply review dispositions. Submission snapshots and audit events are written through the workflow.

The local demo still lacks initiative/form administration, fiscal-year rollover, EIN master-list validation/autofill, exports, production email delivery, and production operations. Role-based user listing is read-only; it does not provision users or edit assignments. The JWT development fallback also requires care: use only a local environment and set an explicit secret outside development.

## Status key

- **Implemented:** the local application behavior is present end to end for the rule's applicable demo scope.
- **Partial:** some supporting behavior exists but the full rule or production obligation is not met.
- **Missing:** no effective implementation was found.
- **Not applicable (local demo):** a production, contractual, or operational obligation outside this demo's runtime; it remains deferred, not satisfied.

## Rule-by-rule assessment

| Rule | Status | Current evidence and remaining gap |
| --- | --- | --- |
| BR-001 Annual initiative portfolio, approximately 175 programs | Partial | Initiative and assignment models exist; no portfolio management or scale validation UI/API. `backend/app/models/__init__.py`; report lookup in `backend/app/services/submission_service.py`. |
| BR-002 At least two reporting collections per initiative/year | Partial | Cycles are stored and open-cycle assignments are queried; no cycle/initiative administration. `ReportingCycle`; `list_available_reports`. |
| BR-003 Narrative, performance, and financial report content | Implemented | Template-backed fields and relational budget lines are loaded, saved, and returned in report details. `validate_form_data`, `persist_submission`, `ReportEditorPage`. |
| BR-004 Common and initiative-specific configurable questions | Partial | Published schemas render and validate supported fields, including section fields; conditional questions and form composition/administration are absent. `get_form_fields`, `validate_form_data`, `ReportEditorPage`. |
| BR-005 Many organizations may be assigned to an initiative | Implemented | `initiative_organizations` supports multiple assignments; assignment lookup is database-backed. No production-scale verification. |
| BR-006 Separate report for each initiative/organization/cycle obligation | Implemented | Draft creation checks assignment and open cycle; the schema uniqueness constraint prevents duplicate instances. `create_draft_submission`; `uq_sub_instance`. |
| BR-007 Multiple individuals may submit for an organization | Implemented | Individual accounts and `user_organizations` membership scope are checked by backend operations. `get_accessible_organization_ids`, `get_submission_for_user`. |
| BR-008 Budget grid supports up to 100 rows | Implemented | Server validation and UI both enforce 100 lines; amounts use decimal arithmetic server-side and integer cents in the UI. `budget_service.py`; `ReportEditorPage`. |
| BR-009 EIN determines an organization's report obligations | Partial | EIN is stored in the organization master and assignments drive report visibility; no Council master-list import or EIN validation workflow. `Organization`; `list_available_reports`. |
| BR-010 Organizations access only their assigned reports | Implemented | Submission read/write/upload/download paths check the current database user and organization membership; Council roles have their defined broader access. `get_submission_for_user`; submission router. |
| BR-011 Individual account-based login | Implemented | Login verifies the active database account and password; identity/role are reloaded from the database. Frontend tokens remain in localStorage. `auth.py`; `dependencies.py`; `useAuth.ts`. |
| BR-012 Multiple uploads, maximum 25 MB each | Partial | Files are read in bounded chunks, capped at 25 MiB, path-scoped, and linked to authorized submissions; filename/content-type checks do not verify actual file content/type. `upload_service.py`; upload/download routes. |
| BR-013 Save work and return later | Implemented | Draft data and budget rows persist to MySQL; the editor autosaves and reloads saved state. `persist_submission`; `ReportEditorPage`. |
| BR-014 Submission confirmation with form snapshot | Partial | Successful submissions create a snapshot and log that confirmation was queued; no email delivery or full snapshot notification is implemented. `persist_submission`; save route. |
| BR-015 Carry forms/layouts into the next fiscal year | Missing | No rollover operation or administration is present. The schema can store versioned templates but does not copy them. |
| BR-016 Preserve renamed/combined initiative lineage | Partial | Relationship records are modeled; no lineage administration or continuity view/rollover flow. `InitiativeRelationship`. |
| BR-017 50–100 internal users with varied permissions | Partial | Four roles and backend role guards exist; capacity testing and user provisioning/permission administration are absent. `require_roles`; `users.py`. |
| BR-018 Indefinite external-user population | Not applicable (local demo) | Production capacity and availability are not tested or established. |
| BR-019 Perpetual submitted-data retention | Partial | Submission snapshots and audit events are written; production retention, backups, recovery, and perpetual operational controls are not configured. |
| BR-020 Council data ownership | Not applicable (local demo) | Contractual ownership and production hosting terms are outside local runtime behavior. |
| BR-021 Require designated fields before submission | Partial | Server validates configured required fields and supported types; conditional visibility/requirements are not implemented. `validate_form_data`. |
| BR-022 Configured financial sum equals its target | Implemented | Server calculates totals and applies the optional published `budget_reconciliation.target`; no target is invented when configuration omits it. `_get_configured_budget_total`; `persist_submission`. |
| BR-023 Validate EIN against Council master list | Partial | Existing organizations are loaded from the database and assignments use those records; no external Council master-list ingestion or validation exists. |
| BR-024 Auto-fill organization details after EIN validation | Missing | Submitter identity is associated with stored organizations, but there is no EIN entry/validation and autofill workflow. |
| BR-025 Breach notification and remediation | Not applicable (local demo) | No production incident-response operation is configured. |
| BR-026 Required production hosting/security environment | Not applicable (local demo) | Local MySQL/filesystem and development servers are not production hosting or compliance evidence. |
| BR-027 February 1, 2027 production go-live target | Not applicable (local demo) | Schedule and contractual delivery readiness are not runtime features. |
| BR-028 Annual Council Finance content review | Not applicable (local demo) | This is an ongoing operational obligation, not a local application function. |
| BR-029 Post-launch support; response within 24 hours is preferred | Not applicable (local demo) | A support contract/process is not part of this demo; the RFP wording is a preference, not an unconditional software SLA. |

## Remaining risks and limitations

1. **JWT configuration:** `backend/app/core/config.py` has a known local development fallback. Keep it local-only and configure a strong secret for any non-development deployment.
2. **Upload content validation:** the byte cap and path checks are enforced, but MIME/content signatures are not independently verified. Do not treat a client-supplied content type as proof of file type.
3. **Administrative scope:** the Council UI offers a review queue and read-only user listing. Form/initiative configuration, user provisioning, annual rollover, analytics visualizations, and export centers are not implemented.
4. **Production obligations:** email, backup/recovery, perpetual retention operations, security certification, production hosting, capacity, and support remain deferred in `ProductionUpdate.md`.

## Verification record

- The user reported a prior successful run of **43 backend tests**. In this Windows sandbox, current backend compile and pytest commands could not start because the configured Python launcher reported “A specified logon session does not exist.” That attempt is not a pass; the backend result for the current tree remains unverified here.
- Current frontend checks pass: **50 tests**, `npm run lint`, and `npm run build`.
- The repository hook could not start because Bash access was denied. This did not replace the frontend checks run directly.
- The ORM contract tests compare table/key structure against the checked-in expected contract; no new live-database metadata query is claimed here.
- The SQL seed is synthetic and intended for an empty local database. It does not create attachment metadata for files that do not exist on disk.

## Next work

1. Add schema-driven form and initiative administration, conditional fields, and fiscal-year rollover while preserving published versions and lineage.
2. Add EIN master-list validation/autofill and explicit Council provisioning flows if required for the demo scope.
3. Add exports, analytics, and notification adapters within the approved local-demo boundary.
4. Plan production hosting, security, capacity, retention/backup/recovery, breach response, and support separately; do not infer production compliance from this demo.
