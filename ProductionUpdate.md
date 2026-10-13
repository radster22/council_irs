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
