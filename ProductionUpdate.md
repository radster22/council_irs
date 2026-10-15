### This File is for HUMANS only, AI AGENTS PLEASE IGNORE

# Production Technology Transition

This file covers how the local prototype moves to production and which business rules are still waiting on that move. Requirement wording stays in [`.claude/rules/02-business-rules.md`](.claude/rules/02-business-rules.md); this file only references rules by ID.

The target platform is AWS GovCloud (US), which meets the FedRAMP High boundary required by BR-026. Every service named below is used inside a Council-owned AWS account with customer-managed KMS keys (BR-020).

## Local prototype to production mapping

| Area | Local prototype (today) | Production (planned) |
| :--- | :--- | :--- |
| Frontend | Vite dev server (`npm run dev`) | `npm run build` output in a private S3 bucket, served through CloudFront with TLS (ACM certificate) and AWS WAF. |
| Backend API | `uvicorn --reload` on port 8000 | Container image in Amazon ECR, run on ECS Fargate with multiple Uvicorn/Gunicorn workers behind an Application Load Balancer. Health checks on the existing `/health` endpoint, rolling deploys with rollback. |
| Database | Local MySQL 8 `council_irs_db` | Amazon RDS for MySQL 8, Multi-AZ, private subnets only, KMS encryption at rest, TLS in transit, automated backups with point-in-time recovery. The schema contract stays the same; schema changes go through a reviewed migration step, never at application startup. |
| File uploads | Repository-root `.uploads/` folder | Private S3 bucket with SSE-KMS, versioning, Block Public Access and Object Lock. `attachments.storage_key` stores the S3 key. The API still authorizes every upload/download, then hands out short-lived presigned URLs. The 25 MiB limit, type allowlist and SHA-256 checksum stay as they are. Existing files are migrated with checksum verification. |
| Upload scanning | Signature and type checks only | GuardDuty Malware Protection for S3 scans each upload before it can be downloaded. |
| Notifications | Confirmation metadata written to the console | Amazon SES with a verified Council sender domain (SPF/DKIM/DMARC), templates, and bounce/complaint handling. |
| Background work | In-process tasks | Amazon SQS queues (with dead-letter queues) consumed by an ECS worker service. Amazon EventBridge Scheduler triggers scheduled jobs. Jobs are idempotent and retried. |
| Configuration and secrets | Local `.env` file | AWS Secrets Manager (DB credentials, JWT `SECRET_KEY`) with rotation; SSM Parameter Store for non-secret settings. Separate dev, test and production accounts. |
| Logging and monitoring | Console output | CloudWatch Logs, metrics and alarms; AWS X-Ray or OpenTelemetry tracing; CloudTrail for every AWS API call. Logs never include secrets, passwords or report contents. |
| Network | localhost | VPC with private subnets for ECS and RDS, VPC endpoints for S3/SQS/Secrets Manager, security groups that allow only ALB → API → RDS. |
| Identity hardening | Email + bcrypt password, JWT | Same account model (BR-011), plus MFA for Council Finance users and optional SSO for Council staff through Microsoft Entra ID (OIDC). |
| Demo data | `database/seed_demo.sql` and demo passwords | Never deployed. Production starts empty and is loaded from the Council Finance master organization list. |
| Build and release | Local checks and the Claude Code pre-commit hook | CI/CD pipeline (GitHub Actions or CodePipeline) runs `compileall`, `pytest`, `npm run lint`, `npm test`, and `npm run build` on every change, then builds and scans the container image before deploy. |
| Backup and recovery | None | AWS Backup with Vault Lock for RDS and S3, cross-region copies, and scheduled restore tests. |

## Business rules still to be completed in production

These rules are partly or entirely missing from the local prototype. Each one is blocked by the local boundary (no email, no queue, filesystem storage), by the frozen database contract, or by scale. The status comes from reading the current code; live MySQL was not checked.

### Blocked by the local boundary (needs cloud services)

1. **BR-014 — Submission confirmation email.** Today only metadata (submission ID, actor, total, line count) is logged to the console. Production: on submit, the API queues a job in SQS; a worker builds the full report copy (HTML body plus PDF attachment) and sends it through SES. Delivery status is logged.
2. **Automated cycle reminders.** Not built. Production: EventBridge Scheduler runs a daily job that finds open cycles with upcoming or passed due dates and incomplete submissions, then queues reminder emails to each organization's contacts through SES. Council Finance sets the reminder schedule per cycle. Storing that schedule needs a database contract decision.
3. **Grid-accurate printable PDF.** Today the browser print dialog ("Print / Save PDF") produces the PDF. Production: a worker renders the report to PDF server-side (headless Chromium or WeasyPrint) using the same grid layout, stores it in S3, and serves it through an authorized presigned URL. The same PDF is reused for the BR-014 email.
4. **Self-service password reset.** Today only Council administrators can reset passwords (BR-017). Production: an emailed, single-use, time-limited reset link sent through SES.
5. **Large exports.** XLSX/CSV exports run inside the API request today. Production: exports run as queued worker jobs that write to S3 and notify the user with a download link, so large fiscal-year exports don't time out.
6. **Master organization list feed (BR-023).** Today an administrator uploads the registry CSV by hand. Production: Council Finance drops the file in a restricted S3 location and a worker runs the same all-or-nothing import, with the result emailed to administrators.

### Blocked by the current database contract (needs an approved schema change)

7. **Immutable audit trail coverage.** `audit_logs.submission_id` is a required foreign key, so only submission events (status changes, admin edits) can be recorded. Logins, autosaves outside a submission, permission changes, password resets and registry imports are not in the audit ledger. Production: make the submission link optional or add a separate system audit table with the same append-only triggers, and also export audit records to an S3 bucket with Object Lock.
8. **BR-008 — Unit cost × quantity and category subtotals.** `budget_line_items` holds only budgeted and actual amounts, and the grid shows grand totals only. Production: add `quantity` and `unit_cost` columns, calculate `subtotal = unit_cost × quantity` on both client and server, and show running subtotals per category.
9. **Reminder schedules and contact records.** Needed for item 2; there is no table for reminder settings or per-organization contacts today.

### Form engine features not yet built

10. **Format masking.** Form fields support text, number, currency, percentage, date, dropdown and boolean types with length and word caps, but there are no input masks for phone numbers or EINs inside report questions.
11. **Embedded data tables in questions.** Questions cannot contain their own tables with row and column calculations; only the budget grid has calculations.
12. **Visual form builder.** Administrators edit form versions as raw JSON (branching through `visible_when` works). Production: a form builder screen on top of the same JSON schema.
13. **Combining initiatives (BR-001 / BR-016).** Rename and retire work, and rollover records `RENAMED` lineage. There is no workflow that merges several initiatives into one and records `COMBINED` lineage.

### Blocked by scale or reporting tooling

14. **Executive visualizations.** The review dashboard shows simple borough spending bars. Production: Checkbook NYC–style dashboards in Amazon QuickSight (available in GovCloud) reading from an RDS read replica, or richer in-app charts using the same analytics API.
15. **BR-018 — External user scalability.** The application has no cap on submitter accounts, but it has not been load-tested. Production: ECS service auto scaling, RDS read replicas for the review queue and exports, and load tests sized for peak due dates with 175 initiatives and 100+ organizations each.
16. **BR-019 — Perpetual retention operations.** Snapshots and audit logs are protected by database triggers. Production adds S3 Object Lock for attachments and exports, AWS Backup Vault Lock, and lifecycle rules that move old files to cheaper storage classes without deleting them.

### Contract and operational rules (no code in the prototype)

17. **BR-020 — Data ownership.** Council-owned AWS account, Council-controlled KMS keys, and a contractual clause that all data and exports belong to the Council.
18. **BR-025 — Breach notification.** Written incident response plan, GuardDuty and Security Hub alerts routed to an on-call rotation, immediate Council notification, and a root-cause and remediation report after any incident.
19. **BR-026 — Hosting boundary.** Deploy only to AWS GovCloud (FedRAMP High) and document the NIST SP 800-53 control mapping. Nothing is hosted on Council servers.
20. **BR-027 — Go-live on February 1, 2027.** Plan backwards from that date: infrastructure build, security review, data load from the master list, user acceptance testing, staff training.
21. **BR-028 — Annual review.** Each year, run the rollover (BR-015) in the test account, review forms and questions with Council Finance, then promote to production.
22. **BR-029 — Support SLA.** Help desk and on-call support with a response target of 24 hours or less, plus testing and training before and after launch.

These are plans, not permission to change the local demo. Do not add production services to the local prototype or change the database schema unless that is explicitly requested.
