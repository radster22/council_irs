# Verification and Change Discipline

- For behavior changes, update focused tests at the layer where the rule is enforced. Cover authorization boundaries, failure cases, and important validation limits.
- Backend checks from repository root: `python -m compileall -q backend/app` and `python -m pytest backend/tests -q`.
- Frontend checks from `frontend/`: `npm run lint`, `npm test -- --run`, and `npm run build`.
- For database-dependent claims, state whether live MySQL was checked. A SQLite suite or checked-in DDL is not live-schema verification.
- Before Claude Code runs a Bash or PowerShell `git commit` command, `.claude/settings.json` invokes `.claude/hooks/pre-commit-checks.mjs`; a failure blocks the commit. The `onFailure: "block"` setting requires Claude Code 2.1.295 or newer. This hook does not replace targeted development checks.
- If a required tool cannot start, report the blocker and leave that check unverified. Do not treat a failed launch, skip, or missing service as a pass.
- For documentation-only changes, validate links/configuration and whitespace; do not run unrelated suites unless required by the hook or user.
