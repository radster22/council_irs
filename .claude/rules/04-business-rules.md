# Confirmed RFP Business Rules

Use this rule with `context/rfp-functional-specs.md`, the Business Rules worksheet, and the live schema reference. These rules describe expected product behavior; they do not authorize changes to the live database contract.

## Requirement Sources

- Treat the RFP as authoritative for contractual requirements. The workbook's user stories and BR-001 through BR-029 are traceability aids; consult cited RFP text when wording or interpretation conflicts.
- Treat the ECI high-level architecture as proposed design context, not as a separate contractual requirement.
- Distinguish local-demo implementation from deferred production obligations. Record deferred production work in `ProductionUpdate.md`.
- Do not invent policy where the RFP is silent. Ask or document the unresolved decision before encoding consequential business behavior.

## Portfolio, Assignments, and Forms

- Support a portfolio that can change annually, at approximately 175 initiatives, with at least two reporting collections per initiative each year.
- Model report obligations per initiative, assigned organization, and reporting cycle. One organization can have multiple initiatives and owes a separate report per assigned initiative; multiple people can submit for an organization subject to access rules.
- Support common and initiative-specific questions and mixed narrative, performance, and financial content. Forms need configurable field types, required fields, conditional questions, and financial tables.
- Determine organization report eligibility using the Council-provided EIN/organization master data and initiative assignments. Validate the organization and scope on every protected backend operation; do not rely on UI filtering.
- Preserve predecessor/successor relationships when initiatives are renamed or combined. Fiscal-year rollover must carry forward prior form questions and layouts without altering historical records.

## Submission and Validation

- Support saving work in progress and returning later. Submission must run authoritative server-side validation for all configured required fields and balancing rules before accepting the report.
- Support review disposition, requests for updates, and resubmission with historical snapshots and immutable audit history. Never overwrite or delete immutable history to represent a later version.
- Trigger the configured submission confirmation after successful submission. The local demo may log notifications to the console; this does not satisfy production email obligations.
- Use `Decimal` for currency, enforce no more than 100 budget lines, and calculate totals on the server. Never trust client-supplied totals, roles, organization IDs, or submission permissions.
- Apply each configured reconciliation rule; a positive total alone is not proof that a report is balanced. Do not assume all budgets reconcile to the same value.
- In published form JSON, `budget_reconciliation` is optional. When present, its `target` may be `"allocated_budget"`, `{ "field_id": "<configured field id>" }`, or `{ "amount": "<decimal string>" }`. Compare the server-calculated line total to that configured target. When absent, do not invent a balancing target.

## Files and Security

- Allow multiple supporting documents per report and enforce the repository's 25 MiB per-file limit. Validate uploads and prevent traversal or unauthorized access to both stored files and report identifiers.
- Enforce account-based individual login and backend role, organization, and initiative authorization on every protected data operation.
- Do not expose filesystem paths, secrets, or sensitive report data through responses or logs. Preserve the live schema's restrictive foreign keys, submission versions, and audit immutability.

## Production-Only Obligations

Track, but do not implement local production infrastructure without explicit approval: government-cloud hosting and FedRAMP/NIST control alignment; capacity and availability commitments; breach notification and response; perpetual retention, backup, and recovery; ongoing annual content review; support response targets; formal testing/training and the February 1, 2027 target go-live. The RFP's preferred response within 24 hours is a preference, not an unconditional service-level guarantee. See BR-017–BR-020 and BR-025–BR-029 in the workbook and the RFP's cited pages.
