# Application Business Rules

This document is the standalone single source of truth (SSOT) for application behavior, rules, and acceptance criteria.

---

## 1. Initiative Portfolio and Reporting Periods

* **BR-001 — Initiative Portfolio Scale**: The system must support a portfolio of approximately 175 unique initiatives, with the total number subject to change each fiscal year. Initiatives must be addable, renamable, combinable, and retirable by fiscal year centrally without rebuilding the application.
* **BR-002 — Reporting Cycles**: Each initiative must support at least two reporting periods per fiscal year (e.g., Mid-Year and Final), with distinct start dates, due dates, and open/closed states.
* **BR-005 — Organization Assignments**: Each initiative must support its assigned reporting organizations, ranging from a single provider to over 100 organizations per initiative.
* **BR-006 — Separate Obligations & Duplicate Prevention**: An organization receiving funding under multiple initiatives must submit a separate report for each initiative and reporting cycle. The system must prevent duplicate submission instances for the same organization, initiative, and cycle.
* **BR-009 — EIN-Based Eligibility**: The system must use an organization's Employer Identification Number (EIN) and its Council assignments to determine and restrict which reports it is required and permitted to submit.
* **BR-016 — Historical Lineage & Predecessor Continuity**: When initiatives are renamed, combined, or restructured, the system must maintain continuity by linking data from successor initiatives to the corresponding predecessor initiatives that preceded them.
* **BR-027 — Production Target Go-Live**: The production platform go-live milestone is February 1, 2027.
* **BR-028 — Annual Review & Lifecycle Maintenance**: The system must accommodate an annual review cycle with Council Finance to review reporting structures, questions, and parameters, and apply required system modifications.

---

## 2. Organizations and User Access Management

* **BR-007 — Multiple Submitters**: Different individuals within the same reporting organization must be permitted to draft, edit, and transmit separate reports for their organization.
* **BR-010 — Strict Access & Organization Isolation**: An organization shall only access initiative reports assigned to it. External submitters are strictly isolated to the organizations linked to their accounts; cross-organization data viewing is prohibited and must be enforced on every backend request.
* **BR-011 — Account-Based Identity**: The system must be account-based, requiring individual login credentials for each person submitting reports. Shared generic accounts are prohibited.
* **BR-017 — Council Finance Administrative Population**: The system must support 50 to 100 administrative users within Council Finance with configurable permission levels, including full administrative oversight, review/edit capabilities, and view-only access. Council administrators must be able to manage accounts, update access levels, and support password resets.
* **BR-018 — External User Scalability**: The system architecture and data model must support an indefinite number of submission-side user accounts without performance degradation.
* **BR-023 — EIN Master Validation**: The system must validate submitted EINs and organization details against an authoritative master organization list provided by Council Finance.
* **BR-024 — Organization Detail Autofill**: Upon validation of an EIN against the master registry, organization details must auto-fill where possible to prevent manual data entry errors.
* **Organization-Wide Shared History**: Authorized external users must be able to view their organization's complete reporting submission history across all funded initiatives, including reports submitted by different colleagues within that organization.

---

## 3. Configurable Reporting Forms & Annual Rollover

* **BR-003 — Comprehensive Report Content**: Reports must support the collection of performance metrics and data, spreadsheet-style financial and budgetary breakdowns, and qualitative narrative descriptions.
* **BR-004 — Central Question Configuration (Common & Unique)**: Forms must support universal questions answered by all organizations as well as questions unique to specific initiatives. Council Finance administrators must be able to update questions, sections, and forms centrally without rebuilding individual reporting forms each year.
* **Dynamic Field Controls**: The form engine must support flexible dropdown menus, rich text and narrative inputs with enforced word/character caps, numeric, currency, and percentage data types with format masking (e.g., phone numbers, EINs).
* **Conditional & Branching Logic**: The form engine must support conditional logic and branching questions so submitters only see questions relevant to their prior responses.
* **Embedded Data Tables**: Questions must support embedded tables with automated column and row calculations.
* **BR-015 — Year-to-Year Rollover Engine**: Council Finance administrators must be able to duplicate prior fiscal year reporting structures, standard questions, initiative-specific questions, and form layouts into a new fiscal year in an automated fashion without rebuilding forms from scratch.

---

## 4. Drafts, Workflow, and Audit Trails

* **BR-013 — Save and Resume**: External users must be able to start a submission, pause work, save progress, and log in later to resume and complete submissions.
* **Autosave Protection**: The application must provide autosave functionality during report editing to protect against data loss. Draft autosaves must not be blocked by transient, incomplete input.
* **BR-019 — Perpetual Retention & Historical Auditability**: All submitted data, versioned form definitions, and historical reports must be retained in perpetuity for audit and historical reference.
* **BR-019A — Council Editing & Review History**: Submitted data must remain editable by authorized Council Finance staff. Council Finance must have the ability to reject reports and/or request updates from submitters, who are then permitted to revise and resubmit. Every revision cycle must preserve previous submission snapshots in version history.
* **Immutable Audit Trail**: The system must maintain an append-only audit ledger recording logins, autosaves, submissions, administrative edits, reviewer notes, and permission changes. Audit logs cannot be updated or deleted.

---

## 5. Spreadsheet Budget Grid & Financial Validation

* **BR-008 — 100-Line Financial Budget Grid**: Financial data must be collected in a format familiar to users of spreadsheet-style budgets, supporting complete itemized spending breakdowns of up to 100 line items.
* **Row-Level & Column Calculations**: The grid must automatically compute row subtotals (`Unit Cost` $\times$ `Quantity` = `Subtotal`) and maintain running category subtotals and grand totals.
* **BR-021 — Pre-Submission Validation**: A report cannot be submitted until every specifically delineated required field, narrative constraint, and data type rule is compliant. The UI must present clear, user-friendly error messages guiding users to correct issues prior to submission.
* **BR-022 — Hard Financial Balancing**: When response fields or budget tables are configured to sum to a specific value (such as the initiative award allocation), the system must enforce that total and prevent submission if the budget is unbalanced or does not equal the required total.

---

## 6. Supporting Documents & File Storage

* **BR-012 — File Upload Constraints**: The system must allow uploading and storage of multiple supporting documents across multiple file formats (e.g., PDF, Excel, Word, CSV). The maximum upload size is strictly 25 MB per file.
* **Document Security & Association**: Supporting files must be associated with the parent submission, track metadata (file name, MIME type, size, SHA-256 checksum), and enforce upload/download authorization so only permitted users can access attachments.

---

## 7. Review, Oversight & Flagged Items Triage

* **Central Oversight Dashboard**: The system must provide Council Finance staff with an internal dashboard to view all submissions and tracking statuses in a centralized location.
* **Multi-Field Filtering & Query**: The dashboard must support filtering, searching, and query-based review across multiple fields (e.g., initiative, organization EIN, borough, fiscal year, cycle, status).
* **Triage / "Flagged Items" View**: The administrative interface must include a dedicated triage view to immediately isolate and monitor:
  1. *Unbalanced Budgets*
  2. *Incomplete Submissions*
  3. *Missing / Overdue Submissions*
  4. *Validation Errors*

---

## 8. Analytics, Exports, and Data Deliverables

* **BR-020 — Council Data Ownership**: All application data ownership remains exclusively with the City Council.
* **Clean MS Office Exports**: Authorized Council Finance staff must be able to extract and export all submitted programmatic and financial data as clean, consistent Microsoft Excel (`.xlsx`) and CSV files fully compatible with Microsoft Office.
* **Grid-Accurate Printable PDF**: Each completed report must be printable and exportable as a PDF that preserves the visual grid-based layout and table formatting of the reporting form.
* **Executive Visualizations & Dashboards**: The system must support generating charts, graphs, and visual dashboards comparable to public financial oversight platforms (e.g., Checkbook NYC) to monitor spending allocations and provider progress.

---

## 9. Automated Communications & Notifications

* **BR-014 — Automated Submission Confirmation**: Upon final submission, the system must automatically dispatch a confirmation email to the submitter containing a complete copy of all information submitted in the report.
* **Automated Cycle Reminders**: The system must support automated reminder emails sent to CBOs and City agencies, configurable by Council Finance staff based on reporting schedules and contact records.

---

## 10. Security, Hosting, and Operational SLAs

* **BR-025 — Data Breach Notification & Remediation**: If hosted infrastructure and/or Council data experiences a security breach, the Council must be informed immediately. The vendor must provide a detailed root-cause remediation report and an actionable plan to eliminate future breach risks.
* **BR-026 — Infrastructure & Compliance Boundary**: The production system will not be hosted on Council-owned servers; a cloud-based implementation is permitted provided it is compliant with either FedRAMP or NIST SP 800-53 standards.
* **BR-029 — Support SLA Turnaround**: The vendor must provide testing, training, and ongoing post-launch technical support with immediate response times, preferably within 24 hours.