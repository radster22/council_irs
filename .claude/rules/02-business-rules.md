# Application Business Rules

This file is the single source of truth for application behavior. It contains the complete functional requirements and acceptance expectations needed to build the system; implementation and agent workflows must not depend on external source documents.

Use **must/shall** requirements as mandatory. **Should** requirements are expected capabilities with softer wording. **Preferred** describes an optional preference. Do not infer new product behavior from technology choices.

## 1. Initiative portfolio and reporting periods

- **BR-001 — Initiative portfolio:** Support a portfolio of approximately 175 initiatives, with initiatives addable, renamed, combined, retired, and changed by fiscal year without rebuilding the application.
- **BR-002 — Reporting cycles:** Each initiative must support at least two reporting periods per year, with distinct start dates, due dates, and open/closed states.
- **BR-005 — Organization assignments:** Each initiative must support its eligible reporting organizations, including more than 100 organizations when assigned.
- **BR-006 — Separate obligations:** An organization funded by multiple initiatives must have a separate submission for each assigned initiative and reporting cycle. Prevent duplicate submission instances for the same organization, initiative, and cycle.
- **BR-009 — EIN eligibility:** Use the organization's EIN and its assignments to determine which reports it is required and permitted to submit.
- **BR-016 — Initiative lineage:** When an initiative is renamed or combined, preserve links from predecessor initiatives to successor initiatives so historical reports remain traceable.

## 2. Organizations and user access

- **BR-007, BR-011 — Individual accounts:** Every person submitting reports must authenticate with an individual account. More than one person may act for an organization.
- **BR-010 — Organization isolation:** External users may access only initiatives, reporting cycles, submissions, history, and attachments assigned to organizations associated with their account. Enforce this on every backend request.
- **Organization history:** An authorized user must be able to see that organization's submission history, including submissions made by other users in the same organization, without exposing other organizations' records.
- **BR-017 — Council access levels:** Support Council Finance accounts with different roles and permissions, including administrators, reviewers, and view-only users. Council Finance must be able to add/manage users, change access levels, and support credential resets.
- **BR-018 — User scale:** Do not impose a fixed application limit on external users. Support the required Council Finance user population of approximately 50–100 people with differing access levels.
- **BR-023 — EIN master validation:** Validate EIN and organization details against the authoritative organization list supplied by Council Finance.
- **BR-024 — Organization autofill:** After EIN validation, prefill organization details available in the authoritative list to reduce user entry errors.

## 3. Configurable reporting forms

- **BR-003 — Report content:** A report must collect the required combination of performance metrics, financial/budget information, and narrative responses.
- **BR-004 — Common and initiative-specific questions:** Forms must support questions shared across initiatives and questions specific to an initiative/report. Council Finance must be able to manage form questions centrally without rebuilding each form.
- Forms must support configurable sections, labels, help text, dropdowns, numeric/currency/percentage fields, narrative fields, and embedded tables.
- Forms must support conditional and branching questions so users see only questions applicable to their responses.
- Council Finance must be able to add initiatives, reports, questions, and form changes through application configuration.
- **BR-015 — Annual rollover:** Authorized Council Finance users must be able to carry prior-year reporting structures and forms into a new fiscal year. Standard questions, initiative-specific questions, and layouts must carry forward while preserving the prior year's records and form versions.

## 4. Draft, submission, and confirmation workflow

- **BR-013 — Save and resume:** Submitters must be able to start, pause, save, and later resume a report. Draft data must persist across sessions, including autosave, without creating a submitted snapshot.
- **BR-021 — Submission validation:** A report cannot be submitted until every configured required field is complete and valid. Validate configured data types, format, and length limits on the backend and show clear, actionable errors.
- A successful submit must persist the submission and a versioned snapshot of form answers and budget rows, record the submitter and time, and make the report available to authorized Council Finance reviewers.
- **BR-019 — Council editing and history:** Authorized Council Finance staff must be able to edit submitted data. Preserve prior snapshots and record changes in an audit/history trail.
- Submitters must be able to revise and resubmit reports returned for updates. Each resubmission must preserve prior versions and review history.

## 5. Budget and financial validation

- **BR-008 — Budget grid:** Provide spreadsheet-style entry for up to 100 budget line items per submission, with clear row/column labels and editable line values.
- **BR-022 — Calculations and configured balance:** Calculate totals automatically. Recalculate amounts and totals on the backend. When Council Finance configures a field/table to sum to a required value, prevent submission unless the configured total is met. Do not impose an unconfigured universal balance target.
- Enforce valid monetary input and use decimal arithmetic. Reject line counts over 100 and invalid configured values before accepting submission.

## 6. Supporting documents

- **BR-012 — Uploads:** A submission must accept multiple supporting files, including common Office, CSV, and PDF formats. Enforce a maximum of 25 MB per file.
- Associate each file with its submission, retain file metadata, and let only users authorized for that submission upload or download it.
- Validate file type/content, size, and storage identifiers; prevent path traversal and unsafe file access.

## 7. Review and Council oversight

- Council Finance must have a centralized view of submissions and reporting obligations.
- Provide search, filtering across multiple fields, and flexible query-based review of initiative, organization, reporting cycle, status, and submission data.
- Provide triage views for unbalanced budgets, incomplete submissions, missing submissions, validation errors, and other items flagged for review.
- Authorized staff must be able to flag items, review a submission, approve it, reject it, or request updates. Enforce these actions by role on the backend.
- Preserve reviewer identity, decision, notes, timestamps, and all prior submission versions in the audit/history trail.

## 8. History, exports, and visualizations

- **BR-019 — Historical records:** Retain submitted data and its history for audit and historical reference. Preserve form versions, submission snapshots, and audit records.
- **BR-020 — Council data ownership:** Keep Council data under Council ownership and provide authorized access and data portability.
- Council Finance must be able to export all collected submission data and responses as clean Microsoft Excel and CSV files.
- Submitters must be able to print or export a completed report to PDF while preserving its grid-based layout.
- Provide Council Finance dashboards and data visualizations, including charts and graphs, for oversight and analysis.
- **Visualization preference:** Capabilities comparable to public accounting/oversight dashboards are preferred; this does not prescribe a particular vendor or library.

## 9. Notifications

- **BR-014 — Confirmation (should):** Send a submission confirmation with the submitted information after the submission is successfully recorded.
- **Reminders (should):** Support automated reminders to reporting organizations based on Council Finance schedules and organization contact records.

