# Security Requirements

- Never read, emit, or commit real credentials, production data, local uploads, generated secrets, or database dumps. Use the root `.env.example` for placeholders; keep `.env` ignored. Synthetic demo credentials may appear only in the local seed and clearly labeled local-demo documentation.
- Treat client IDs, roles, organization membership, totals, and permissions as untrusted. Reload user identity/role from the database and authorize every backend operation.
- Enforce role, organization, initiative, and submission scope on reads, writes, review actions, upload, and download. Hiding a UI control is not authorization.
- Validate upload size (25 MiB maximum), accepted content/type, generated storage key, and resolved path. Prevent path traversal and authorize every attachment against its submission.
- Use parameterized database access and least privilege. Do not log secrets, credentials, sensitive form content, or unnecessary local paths.
- Inspect a live schema only with read-only queries. Do not run destructive SQL during audits.
- Preserve immutable audit/version records and restrictive relationships. Do not weaken triggers, foreign keys, or `RESTRICT` delete behavior as an application workaround.
- Use synthetic or masked data in tests. Do not copy production data into local or test environments.
