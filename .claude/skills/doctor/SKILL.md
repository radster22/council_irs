---
name: doctor
description: Check repository setup, configuration, and common development prerequisites.
---

# Repository Doctor

Inspect the repository structure, required environment variables, dependency manifests, and available test commands. Report concrete blockers and safe next steps. Do not modify production data or secrets.

## Required workflow

1. Read the relevant `.claude` instructions and repo docs before editing.
2. Check the backend dependency manifests and env placeholders.
3. Validate with the smallest relevant command, such as `python -m pytest backend/tests -q` or `python -m compileall -q backend/app`.
4. Record blockers explicitly and avoid claiming a service is verified unless the command output shows it.

## Do not do

- Do not read or commit secrets from `.env` files.
- Do not change live production database content.
- Do not treat missing MySQL credentials as a successful database validation.