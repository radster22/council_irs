# Production Update Plan

## Purpose

Document infrastructure, security, reliability, and deployment changes deferred from the local demonstration. These items must not be implemented during the current demo phase unless explicitly approved.

## Current Demo Configuration

| Concern               | Local implementation               |
| --------------------- | ---------------------------------- |
| Database              | Locally installed MySQL 8+         |
| File storage          | Local filesystem under `.uploads/`  |
| Notifications         | Python console logging             |
| Background tasks      | FastAPI/Starlette in-process tasks |
| Service orchestration | Manual local startup               |
| Frontend              | Vite development server            |
| Backend               | Uvicorn development server         |

## Deferred Production Work

### 1. Object Storage

* Replace local filesystem storage with MinIO or a managed S3-compatible object store.
* Migrate existing files and verify checksums.
* Configure private buckets, least-privilege credentials, and authorized downloads.
* Define backup, retention, and recovery procedures.

### 2. Background Processing

* Evaluate Redis and Celery or an equivalent durable job-processing system.
* Move scheduled reminders, large exports, and retryable work out of process.
* Add retry policies, task monitoring, failure handling, and idempotency.
* Ensure critical jobs survive application restarts.

### 3. Email Delivery

* Replace console notifications with an approved SMTP or email provider.
* Add delivery-failure handling, retry policies, and notification auditing.

### 4. Deployment and Operations

* Define production hosting and service orchestration.
* Configure HTTPS, reverse proxy, secrets management, and environment-specific settings.
* Establish structured logging, monitoring, alerting, and health checks.
* Document database and file-storage backup and restoration.

### 5. Security and Compliance

* Complete a security review against applicable Council requirements and the selected hosting environment.
* Evaluate required NIST 800-53 or FedRAMP-aligned controls with the responsible stakeholders.
* Review access control, audit retention, encryption, vulnerability management, and incident response.
* Validate the production environment before handling real Council data.

### 6. RFP-Specific Production Obligations

These obligations are summarized from BR-017 through BR-029 in the supplied Business Rules worksheet and its cited RFP pages. They are not satisfied by the local demonstration:

* Size and validate capacity for 50–100 Council Finance users with varied permissions and an indefinite submission-side population; establish availability and performance targets.
* Establish Council data ownership, data export/portability, perpetual retention, backup, recovery, and integrity-check procedures.
* Define breach notification, remediation reporting, and future-risk-reduction processes with Council stakeholders.
* Plan the formal pre-launch testing/revision and training periods around the RFP target go-live date of February 1, 2027.
* Provide the annual Council Finance review of reporting structure/content and a contracted post-launch support model. Treat the RFP's “preferably within 24 hours” response wording as a preference pending a defined service agreement, not as an already established SLA.

The local demo must not claim that these production obligations are met. Confirm exact contractual interpretation against the RFP text before establishing production commitments.

## Scope Guard

Do not add Redis, Celery, MinIO, a production email provider, Docker-based orchestration, or production deployment configuration to the demo unless explicitly authorized.

This document records future work; it does not certify that the local demo or a future deployment meets production compliance requirements.
