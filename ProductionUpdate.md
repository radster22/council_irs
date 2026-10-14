### This File is for HUMANS only, AI AGENTS PLEASE IGNORE

# Production Technology Transition

This file is limited to technology changes needed to move the local demonstration stack to a production deployment. Application behavior requirements remain in [`.claude/rules/02-business-rules.md`](.claude/rules/02-business-rules.md).

## Current local stack

- Vite development server and local frontend build.
- FastAPI/Uvicorn development server.
- MySQL database configured for the local demonstration.
- Uploads stored on the application filesystem.
- Notifications written to the application console.
- Background work runs in-process.
- Local `.env` configuration.

## Production technology changes

- **Hosting and network:** Select an approved non-Council-hosted production environment. Configure production DNS, TLS, reverse proxy/load balancing, network boundaries, and separate development/test/production configuration.
- **Application deployment:** Replace development servers with a supported production serving/deployment setup. Build and serve the frontend as production assets; configure health checks, controlled releases, rollback, and environment-specific settings.
- **Secrets:** Move credentials and signing/encryption keys from local environment files into a managed production secrets service with access control and rotation.
- **Database:** Provision a production MySQL service with restricted networking, encryption, backups, restoration testing, monitoring, and a validated connection/configuration. Keep the existing schema contract unchanged unless separately authorized.
- **File storage:** Replace local filesystem uploads with private, durable object storage. Migrate files with checksum verification and retain authenticated per-submission access controls.
- **Background jobs:** Move reminders, exports, and retryable asynchronous work from in-process tasks to a durable queue/worker service with retries, failure monitoring, and idempotent processing.
- **Email:** Replace console notifications with an approved delivery provider; configure sender identity, templates, delivery-failure handling, and audit-safe logs.
- **Observability:** Add centralized application/platform logs, metrics, traces, alerts, and service-health monitoring without logging secrets or report contents.
- **Security platform:** Select and validate the required hosting security boundary and controls, including vulnerability/dependency management, encryption, malware scanning for uploaded files, and incident telemetry.
- **Capacity and resilience:** Size the environment for initiative/reporting-period peaks and required user populations. Define and validate availability, backup, recovery, and scaling configurations.

These are production stack transitions, not authorization to change application scope or the existing database schema. Do not add production services to the local demo unless explicitly requested.




## Future updates

The following features and operational requirements are deferred beyond the local demo scope and will be moved to a post-demo technical roadmap:

1. **User Account Creation Portal (BR-011 / BR-017)**:
   - Implementing a self-service registration or admin modal for in-app user provisioning (`POST /api/admin/users`). Currently, accounts are pre-seeded in `database/seed_demo.sql`.
2. **Master Organization Registry UI (BR-023)**:
   - Dedicated frontend interface for Council staff to create and edit master organization records in `organizations`. The backend API (`POST /api/admin/organizations`) exists but is not rendered in the frontend.
3. **Interactive Submitter EIN Lookup & Autofill (BR-023 / BR-024)**:
   - Submitter-facing lookup search box to query an unassigned EIN against the master list and auto-fill legal name and borough. Currently, submitters are pre-assigned by their login account.
4. **Visual Drag-and-Drop Form Builder & Branching (BR-004)**:
   - Visual dynamic form builder replacing raw JSON template entry; dynamic question branching/conditional visibility; embedded calculation tables within questions.
5. **Automated Reminders Engine**:
   - Automated cron/scheduler service to dispatch reminder emails for upcoming cycle deadlines based on contact records.
6. **Audit Log Scope Expansion (BR-019)**:
   - Decoupling `audit_logs.submission_id` to allow tracking user-level authentication events, password changes, and permission adjustments without violating foreign key constraints.
7. **Budget Quantity and Unit Cost Model (BR-008)**:
   - Adding `quantity` and `unit_cost` columns to `budget_line_items` to capture unit-rate calculations (`qty * unit_cost = amount`) directly in the database.
8. **Production Security & Governance (BR-020, BR-025, BR-026, BR-027, BR-029)**:
   - Cloud migration to FedRAMP/NIST SP 800-53 compliant infrastructure (AWS GovCloud / Azure Government).
   - Formal incident response plans and Council breach notification workflows.
   - Ongoing support SLA management and contractual data ownership agreements.
