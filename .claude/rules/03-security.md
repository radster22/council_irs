# Security Rules

- Never commit real/production secrets, credentials, production data, or uploaded files. Synthetic local-demo credentials may appear only in the explicitly approved seed script and must be labeled local-only.
- Validate and authorize every externally supplied identifier and file operation.
- Use parameterized database queries and enforce least-privilege access.
- Avoid logging sensitive personal, financial, or authentication data.
- Treat all user-supplied IDs, roles, organization IDs, and submission permissions as untrusted until validated server-side.
- Use read-only database inspection and avoid destructive SQL commands while auditing the live schema.
- Keep `.env`, local uploads, and generated files out of source control; use `.env.example` for placeholders only.
- Do not expose upload paths or internal database details through the application layer or logs.
