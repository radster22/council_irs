# RFP Functional Specifications

This is the confirmed working summary of business requirements for the local demonstration and eventual production system. The detailed 29-rule traceability assessment is in `business_rules/COMPLIANCE_DIAGNOSTIC.md`.

## Requirement Source Hierarchy

1. The RFP is authoritative for contractual requirements and scope. Its cited page references are recorded in the Business Rules worksheet.
2. `business_rules/NYC_Council_Initiative_Reporting_User_Stories_and_Business_Rules.xlsx` provides user stories and a 29-rule summary traced to the RFP; consult the cited RFP text if interpretation or wording conflicts.
3. `business_rules/ECI_NYC_Council_Initiative_Reporting_High_Level_Architecture.docx` describes a proposed architecture. It is design context, not a separate contractual commitment.
4. The live MySQL schema remains authoritative for persistence contracts. Preserve its keys, triggers, immutable records, and types; do not infer permission to change it from a functional requirement.

## Confirmed Functional Requirements

- Support a changing portfolio of approximately 175 initiatives, at least two reporting cycles per initiative each year, multiple assigned organizations, and separate reports for each initiative/organization/cycle obligation (RFP pp. 6, 8; BR-001–BR-007).
- Support mixed narrative, performance, and financial report content, including common and initiative-specific questions and configurable required-field, conditional, and balancing validation (RFP pp. 6–7, 12–13; BR-003–BR-004, BR-021–BR-022).
- Support up to 100 budget lines with server-authoritative decimal calculations and reconciliation (RFP p. 7; BR-008, BR-022; see `.claude/rules/02-budget-calculations.md`).
- Apply reconciliation only when the published form configures a target. The current JSON form convention uses optional `budget_reconciliation.target`: `"allocated_budget"`, `{ "field_id": "<configured field id>" }`, or `{ "amount": "<decimal string>" }`. A missing rule does not imply a universal target.
- Use person-specific accounts and Council Finance-provided EIN/organization information to determine assigned report eligibility; enforce role, organization, and initiative scope on the backend (RFP pp. 8, 11, 13; BR-009–BR-011, BR-023–BR-024).
- Allow work in progress to be saved and resumed; validate required fields before submission; support review, requests for updates, and resubmission while preserving historical submissions and audit records (RFP pp. 8–12; BR-013, BR-021; live schema reference).
- Accept multiple supporting files per report up to 25 MiB each, validate them, and prevent path traversal (RFP pp. 8, 11; BR-012; repository security rule).
- Carry forward forms and layouts between fiscal years, and preserve initiative lineage after renames or combinations (RFP pp. 9–10; BR-015–BR-016).
- Provide submission confirmation, reporting and exports, dashboard oversight, and required retention consistent with the RFP (RFP pp. 8–12; see user stories and cited rules in the workbook).
- Preserve City Council data ownership. Production hosting, security compliance, breach response, capacity, ongoing annual review, support, and go-live obligations are production concerns and must be tracked in `ProductionUpdate.md`; do not introduce production infrastructure into the local demo without explicit approval (RFP pp. 5, 7–10, 12; BR-017–BR-020, BR-025–BR-029).

## Local-Demo Boundary

Local storage, console notifications, and lightweight in-process work are the current demo architecture. These choices do not satisfy or waive production RFP obligations. Mark deferred production requirements explicitly instead of describing them as implemented. No database schema or trigger changes are authorized by these functional requirements.
