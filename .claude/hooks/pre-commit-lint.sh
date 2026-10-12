#!/usr/bin/env sh
set -eu

# Run the fastest repo-level validation that matches the current project state.
if [ -d backend ]; then
  python -m compileall -q backend/app
  python -m pytest backend/tests -q || exit 1
fi

if [ -f frontend/package.json ]; then
  (cd frontend && npm run lint --if-present)
fi

# Keep project hygiene aligned with the repo rules.
if [ -f .gitignore ]; then
  git diff --check -- . ':!*.env' ':!**/.env' || true
fi