# Project Diagnostics

**Review date:** 2026-10-13

**Scope:** Rechecked the current frontend, backend, demo seed, ORM contract, setup guidance, and earlier findings. `.claude/rules/02-business-rules.md` is the requirements SSOT. No confidential source attachments, `.env` values, uploaded files, or database dumps were opened. No live MySQL connection was used and no SQL was executed.

## Summary

This update fixes the unavailable admin action styling and several local-demo gaps: clean seed data now includes an unstarted overdue report and repairable unbalanced drafts; administrators can add registry organizations and provision scoped user accounts; the Council queue supports the missing filter dimensions and exposes validation reasons; and uploads check common file signatures. The ORM declares the four existing check constraints and the dependency manifest directly pins Pydantic v2.

The local application has database-backed reporting, role and organization checks, review dispositions, history, upload/download, admin setup, annual rollover, conditional fields, reporting filters, exports, and browser printing. No check in this report proves the connected MySQL schema matches the checked-in schema contract.

## Verification

| Check | Result |
| --- | --- |
| Backend `\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider` | Passed: 58 tests, 2 dependency deprecation warnings. |
| Backend `\.venv\Scripts\python.exe -m compileall -q backend/app` | Passed. |
| `npm run lint` (`frontend/`) | Passed. |
| `npm test -- --run` (`frontend/`) | Passed: 50 tests. |
| `npm run build` (`frontend/`) | Passed. Generated CSS contains `.bg-brand-600` and `.border-brand-300`. |
| XLSX API export | Passed as part of the backend suite. `pandas` and `openpyxl` are declared in `requirements.txt`. |
| `git diff --check` | Passed for the current refresh. |
| Live MySQL metadata comparison, seed execution, seeded-account login | Not performed. |

The default `python` and `py -3.12` launchers fail with a Windows logon-session error in this environment. Invoking the repository interpreter directly works; backend results above use that interpreter.

## Changes made in this refresh

- Added configured Tailwind `brand-300` and `brand-600`; the “Initiatives & forms” link now renders with the expected blue background and readable white text.
- Added a distinct Staten Island organization and submitter. This submitter has an open unstarted report whose due date is intentionally past; it remains open so the report can still be started in the demo.
- Seeded two incomplete, unbalanced drafts, including a zero-value placeholder row, plus the previously seeded unbalanced submitted report. Submitters can correct the draft form and budget in the editor.
- Added an overdue badge and `is_overdue` result for open unstarted obligations.
- Added Council-admin UI and API flows for creating an organization in the EIN registry and provisioning an account with validated role and organization membership.
- Added Council queue filters for EIN, borough, fiscal year, initiative, and reporting cycle, and exposed validation reasons in the queue. Added single-field `equals`/`not_equals` conditional questions with backend validation.
- Added signature checks for PDF, common image formats, legacy Office documents, and XLSX/DOCX package contents; text uploads reject NUL bytes.
- Declared the existing lineage, cycle-date, budget-line range, and attachment-size checks in SQLAlchemy metadata. No SQL schema or trigger was changed.
- Added a direct Pydantic v2 dependency constraint.
- Removed source-document citations/attribution from the standalone requirements and skills, removed the source-document reference from `AGENTS.md`, and aligned the architecture rule with BR-026.
- Updated README demo credentials and seeded-case descriptions.

## Remaining findings

### Local application behavior

1. **Form configuration is not a complete dynamic form engine.** Versioned JSON templates support basic fields and one-field `equals`/`not_equals` visibility conditions, enforced in the UI and backend. Section-aware layout, shared-question composition, richer branching, and embedded calculated tables remain unimplemented. Published form versions are preserved.
2. **Submitter EIN validation/autofill is still absent.** Council admins can add an organization with a format-checked EIN and provision accounts from active registry records. The application does not independently verify a newly entered EIN against an external authoritative source, nor does the submitter portal offer an EIN lookup/autofill workflow.
3. **Audit coverage is bounded by the current schema.** Submission, review, and Council-edit events create submission-linked audit rows. Login, autosave, and account/permission changes are not recorded. `audit_logs.submission_id` is required; user-only events need a deliberate schema-contract decision.
4. **Budget row calculations do not include unit cost multiplied by quantity.** Existing rows store category, description, budgeted amount, and actual amount. Adding quantity/unit-cost columns changes the database contract; Decimal-based totals and configured reconciliation are present.
5. **Production communication and PDF behavior are not implemented locally.** Confirmations are logged to the console; full-snapshot email and scheduled reminder email are absent. Reports use browser printing; there is no dedicated grid-faithful PDF generator.
6. **Upload malware scanning is absent.** Common file signatures are checked in addition to size, declared MIME/extension, generated paths, and authorization. Signature checks do not establish that a file is safe to open.
7. **Analytics remain summary-level.** Status counts, budget totals, and borough totals are shown; broader progress/spending visualizations are not available.

### Production-only and database verification limits

- Production hosting, compliance validation, breach response, service capacity, support commitments, durable reminders, managed secrets, backup/recovery, and persistent object storage cannot be demonstrated by this local app. Technology transition notes remain in `ProductionUpdate.md`.
- SQLite tests do not execute MySQL triggers or prove that a connected live schema matches `database/schema.sql` and SQLAlchemy metadata.
- The seed is intended for an empty disposable local database. Run it against the intended local MySQL version and verify the demo logins before relying on live behavior.

## Business-rule status matrix

“Implemented” means supported by the checked-in local application and tests; it does not certify the live database or production deployment.

| Rule | Status | Evidence and limit |
| --- | --- | --- |
| BR-001 Initiative portfolio | **Partial** | Initiative create/update and rollover exist; no general merge workflow or ~175-initiative scale test. |
| BR-002 Reporting cycles | **Partial** | Cycles and dates are configurable; no automatic open/close scheduler. |
| BR-003 Report content | **Partial** | Metrics, narratives, budget rows, and basic conditional fields exist; embedded calculated tables do not. |
| BR-004 Common and initiative forms | **Partial** | Versioned initiative templates and basic conditional visibility exist; no shared-question composition, section-aware layout, embedded tables, or visual schema editor. |
| BR-005 Organization assignments | **Partial** | Active registry organizations can be assigned; no high-volume assignment test. |
| BR-006 Separate obligations and duplicate prevention | **Implemented** | Availability derives from assigned open cycles; duplicate organization/initiative/cycle reports are prevented. |
| BR-007 Multiple submitters | **Partial** | Admins can create individual users and link multiple people to an organization; users share the one report instance allowed for an organization/initiative/cycle. |
| BR-008 100-line financial grid | **Partial** | 1–100 lines, amounts, and totals exist; unit cost × quantity is absent from the existing schema/UI. |
| BR-009 EIN-based eligibility | **Implemented** | Backend access derives from user memberships and initiative assignment checks. |
| BR-010 Organization isolation | **Implemented** | Submission and attachment access use current identity and membership checks; focused tests exist. |
| BR-011 Account-based identity | **Implemented** | Admins can provision individual password-hashed accounts; external accounts require active organization memberships. |
| BR-012 Supporting documents | **Partial** | File-size/type/signature checks, metadata, path safety, and access controls exist; malware scanning does not. |
| BR-013 Save and resume | **Implemented** | Drafts persist, retain incomplete values, and can be resumed. |
| BR-014 Submission confirmation | **Partial** | Receipt and console confirmation logging exist; full-copy confirmation email does not. |
| BR-015 Annual rollover | **Partial** | Rollover copies initiatives, cycles, eligibility, and versioned forms; durable retry/recovery is absent. |
| BR-016 Historical lineage | **Partial** | Rollover records predecessor/successor links; no general combine/split workflow. |
| BR-017 Council administration | **Partial** | Existing account updates, provisioning, password reset, membership changes, and organization registry creation exist; Council-scale performance is untested. |
| BR-018 External-user scalability | **Partial** | Relational membership model has no fixed account cap; no performance/capacity evidence. |
| BR-019 Perpetual retention and auditability | **Partial** | Submission versions and audit rows are protected by schema triggers; login, autosave, and permission changes are not represented. |
| BR-019A Council edit and review history | **Implemented** | Review dispositions and Council edits retain snapshots and audit records. |
| BR-020 Council data ownership | **Not applicable to local verification** | Legal ownership is not established by this code review. |
| BR-021 Pre-submission validation | **Partial** | Required fields, types, limits, conditional visibility, budget rows, and reconciliation are checked; complex branching and embedded table validation remain absent. |
| BR-022 Hard financial balancing | **Partial** | Server uses Decimal and enforces configured targets; unit-cost/quantity row calculations are unavailable. |
| BR-023 EIN master validation | **Partial** | Admin registry creation checks EIN format/uniqueness and assignments resolve active entries; independent authoritative verification is absent. |
| BR-024 Organization detail autofill | **Missing** | Submitter-facing EIN lookup/autofill is not implemented. |
| BR-025 Breach notification and remediation | **Not applicable to local verification** | Operational incident-response commitments are not demonstrated locally. |
| BR-026 Hosting and compliance boundary | **Not applicable to local verification** | Production hosting/compliance controls are not established by the local stack; guidance wording now aligns with the SSOT. |
| BR-027 Production go-live target | **Not applicable to local verification** | Local code checks cannot establish a production milestone. |
| BR-028 Annual review and lifecycle maintenance | **Partial** | Configuration and rollover exist; no annual review workflow/checklist. |
| BR-029 Testing, training, and support SLA | **Not applicable to local verification** | Vendor support commitments cannot be verified in this app. |

### Additional capabilities

| Capability | Status | Evidence and limit |
| --- | --- | --- |
| Council filters | **Implemented** | Search plus status, balance, EIN, borough, fiscal year, initiative, and cycle filters are available. |
| Flagged and overdue triage | **Partial** | Incomplete validation reasons, unbalanced reports, open obligations, and overdue badges are visible; there is no separate dedicated triage workspace. |
| CSV and Excel exports | **Implemented** | CSV bundle and XLSX workbook routes are implemented; XLSX test passed. |
| Grid-accurate PDF | **Partial** | Browser print/save-as-PDF is available; layout fidelity is not established by a dedicated exporter. |
| Visualizations | **Partial** | Status/budget summaries exist; broader initiative-progress visuals do not. |
| Automated reminders | **Missing** | No reminder scheduler or email dispatch path exists. |

## Recommended next work

1. Add conditional form rules and embedded table fields without changing published schemas in place.
2. Decide whether the live database contract may change before implementing unit-cost/quantity columns or user-level audit events.
3. Define an approved source and workflow for authoritative EIN verification and submitter detail autofill.
4. Keep full-snapshot emails, reminders, dedicated PDF generation, malware scanning, hosting, and operations within approved production work.
5. Run the demo seed and README login flow against an isolated local MySQL instance before claiming live compatibility.