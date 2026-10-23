# Bug Fix Log

Bug fixes made in this project with AI coding agents, from the initial commit (`0228562`, 2026-10-12) to `73583f2` (2026-10-15).

## How this log was built

- **Sources:** git history (each commit's diff), the earlier versions of `PROJECT_DIAGNOSTICS.md` stored in git (audits from 2026-10-13 and 2026-10-14), and the current code.
- **Bugs only.** An entry is something that behaved wrongly, was unsafe, or contradicted the documentation. New features that closed requirement gaps (user creation, rollover, exports, filters, EIN autofill) are not counted. Refactors (CSS classes, removing dead code) and repository cleanup are not counted.
- **Agent attribution.** Commits `cfaba72` and `5dbb6c1` carry an AI co-author line. The earlier commits (`b1c6458`, `64691b3`, `e3eb3cc`, `5788584`) were committed without one; this log treats them as agent work because the matching audit files show agent-driven review and fix passes.
- **Verification.** Live MySQL was never checked for any of these fixes. Backend results come from the SQLite test suite.

## Priority scoring

Each bug is scored 1 (low) to 5 (high) on five characteristics:

| Characteristic | What it measures |
| :--- | :--- |
| **Impact** | How bad the outcome was: data loss, security exposure, blocked workflow, or cosmetic. |
| **Reach** | How many users or flows were affected. |
| **Complexity** | How hard the root cause was to find and fix correctly. |
| **Effort** | How much code and testing the fix needed. |
| **Detectability** | How likely it was to go unnoticed (5 = silent until it causes damage). |

**Priority score = Impact × 2 + Reach + Complexity + Effort + Detectability** (maximum 30). Impact counts double because it decides how much the bug matters. Score ranges: **Critical** 23+, **High** 18–22, **Medium** 13–17, **Low** 12 or below.

## Ranked summary

| Rank | ID | Bug | Commit | Impact | Reach | Complexity | Effort | Detect. | Score | Priority |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | BUG-01 | Uploads accepted any file type | `e3eb3cc`, `5788584` | 5 | 4 | 3 | 3 | 4 | 24 | Critical |
| 2 | BUG-02 | Draft autosave blocked by incomplete budget input | `e3eb3cc` | 4 | 5 | 4 | 4 | 3 | 24 | Critical |
| 3 | BUG-03 | Schema setup file dropped the whole database | `5dbb6c1` | 5 | 5 | 2 | 1 | 5 | 23 | Critical |
| 4 | BUG-04 | EIN format mismatch in assignment; duplicate organizations possible | `cfaba72` | 4 | 3 | 3 | 3 | 4 | 21 | High |
| 5 | BUG-05 | Uploads stored in the wrong folder and committed to git | `64691b3` | 3 | 4 | 2 | 2 | 4 | 18 | High |
| 6 | BUG-06 | Oversized upload gave no visible error | `cfaba72` | 3 | 4 | 2 | 3 | 3 | 18 | High |
| 7 | BUG-07 | Budget grid lost typing focus on every keystroke | `cfaba72` | 3 | 5 | 3 | 1 | 2 | 17 | Medium |
| 8 | BUG-08 | Revision-request comment never shown to the submitter | `cfaba72` | 3 | 4 | 2 | 2 | 3 | 17 | Medium |
| 9 | BUG-09 | Demo seed had no report a submitter could start | `5788584` | 3 | 4 | 2 | 2 | 3 | 17 | Medium |
| 10 | BUG-10 | Budget validation API had no login check | `e3eb3cc` | 3 | 3 | 1 | 1 | 5 | 16 | Medium |
| 11 | BUG-11 | Error messages shown as raw JSON | `cfaba72` | 2 | 5 | 2 | 2 | 2 | 15 | Medium |
| 12 | BUG-12 | ORM missing database check constraints; Pydantic v2 not pinned | `5788584` | 2 | 2 | 2 | 2 | 4 | 14 | Medium |
| 13 | BUG-13 | Configuration split across two `.env` files; JSON header sent on GET requests | `b1c6458` | 2 | 3 | 2 | 2 | 2 | 13 | Medium |
| 14 | BUG-14 | Printed reports lost table borders | `cfaba72` | 2 | 3 | 1 | 1 | 2 | 11 | Low |
| 15 | BUG-15 | "Initiatives & forms" button invisible | `5788584` | 2 | 2 | 2 | 1 | 2 | 11 | Low |

Rows are ordered by score; ties are broken by impact, then reach.

**Read the scores together with the characteristics.** BUG-03 (dropping the database) scores slightly below BUG-01 and BUG-02 only because it was a one-line fix. By outcome alone it was the most dangerous bug, since it would have destroyed records the system must keep forever. BUG-10 (missing login check) scores Medium because it exposed no stored data, but it was still a security-boundary failure.

---

## Detailed entries

### BUG-01 — Uploads accepted any file type (Critical)

- **Fixed in two steps:** `e3eb3cc` (2026-10-13), then `5788584` (2026-10-13).
- **File:** `backend/app/services/upload_service.py`
- **Symptom:** The server stored any file and trusted the content type sent by the browser. An executable or script renamed to `.pdf` would be accepted and later served to Council staff. This broke BR-012 (allowed formats) and the security rules.
- **Root cause:** `save_uploaded_file` checked size and path safety but never checked the file's extension, declared type or actual bytes.
- **Fix:**
  1. `e3eb3cc` added an allowlist that matches each extension to its permitted content types (PDF, CSV, XLS/XLSX, DOC/DOCX, TXT, JPG, PNG). Anything else is rejected with "File extension and content type are not allowed."
  2. `5788584` added `_validate_file_signature`, which checks the first bytes of PDFs, images and legacy Office files and the internal package layout of XLSX/DOCX. CSV and TXT files containing NUL bytes (binary content) are rejected.
- **How it went:** The first audit flagged it as High. The first fix still trusted the browser's declared type, so the next audit flagged spoofing and the signature check followed. Malware scanning remains production work (`ProductionUpdate.md`).
- **Verification:** Backend upload tests for rejected types, mismatched signatures and CSV binary content.

### BUG-02 — Draft autosave blocked by incomplete budget input (Critical)

- **Fixed:** `e3eb3cc` (2026-10-13).
- **File:** `backend/app/services/submission_service.py`
- **Symptom:** While a submitter was typing a budget amount (blank field, "12.", etc.), autosave failed. The editor stayed in "unsaved" state and kept retrying, and the work could be lost. This broke BR-013 (save and resume) and the autosave rule that "draft autosaves must not be blocked by transient, incomplete input."
- **Root cause:** `persist_submission` ran the strict submit-time budget validation on every save, including drafts.
- **Fix:** Drafts now go through a separate lenient check (`_validate_draft_budget_lines` and `_optional_draft_decimal`) that accepts partial values. The draft rows are saved as typed in `form_data["_draft_budget_lines"]` so they reload exactly as entered. Strict validation still runs on final submission, and the draft-only key is removed before submitted data is stored.
- **How it went:** Took the most design work of any fix, because draft state had to be stored without changing the database schema and without letting bad values reach submitted records.
- **Verification:** Backend tests for saving drafts with incomplete amounts and for strict rejection on submit.

### BUG-03 — Schema setup file dropped the whole database (Critical)

- **Introduced:** `9beaee3` (2026-10-14). **Fixed:** `5dbb6c1` (2026-10-14).
- **File:** `database/schema.sql`
- **Symptom:** The first line of the setup script became `DROP DATABASE IF EXISTS council_irs_db;`. Anyone running the file to set up or "refresh" tables would silently delete every submission, version snapshot and audit log.
- **Root cause:** A reset step that belongs only in the README's manual rebuild instructions was added to the schema file itself. That contradicted the file header, the security rule against destructive SQL, and BR-019 (perpetual retention).
- **Fix:** Removed the line so the file only creates objects again. The destructive reset stays in the README, with warnings to use it only on a disposable local database.
- **How it went:** Found during the third audit pass the same day it was introduced. One-line fix, but the highest risk in the project because it destroys data the system is required to keep forever.
- **Verification:** `git diff` shows the original line restored. Not run against MySQL.

### BUG-04 — EIN format mismatch in assignment; duplicate organizations possible (High)

- **Fixed:** `cfaba72` (2026-10-14).
- **Files:** `backend/app/routers/admin.py`, new `backend/app/services/organization_service.py`
- **Symptom:** Assigning an organization with EIN `456789012` failed when the registry stored `45-6789012`. Creating an organization with the other format could create a duplicate of an existing EIN.
- **Root cause:** EINs were compared as raw strings with no normalization.
- **Fix:** Added `normalize_ein` and `find_organization_by_ein`, which accept either format. Assignment, organization creation and the new registry lookup all use them, and a duplicate creation returns 409.
- **How it went:** Found while building EIN registry validation (BR-023/024). The same helpers became the base of the registry import and autofill features.
- **Verification:** Two backend tests (match across formats, duplicate rejected).

### BUG-05 — Uploads stored in the wrong folder and committed to git (High)

- **Fixed:** `64691b3` (2026-10-13).
- **Files:** `backend/app/services/upload_service.py`, `.gitignore`
- **Symptom:** Uploaded files were written to `backend/.uploads/` instead of the repository-root `.uploads/`. That folder wasn't ignored, so four demo PDFs were committed to the repository.
- **Root cause:** `UPLOAD_ROOT` used `parents[2]`, which resolves to `backend/` rather than the repository root.
- **Fix:** Changed to `parents[3]` (repository root), deleted the committed upload files, and relied on the root `.uploads/*` ignore rule.
- **How it went:** Easy fix once found. The risk was that real uploaded documents would be pushed to GitHub, which the security rules forbid.
- **Verification:** New test `test_upload_storage_root_is_repository_dot_uploads`.

### BUG-06 — Oversized upload gave no visible error (High)

- **Fixed:** `cfaba72` (2026-10-14).
- **File:** `frontend/src/routes/ReportEditorPage.tsx`
- **Symptom:** Choosing a file over 25 MB seemed to do nothing. The error went to a shared banner at the bottom of Step 4, far from the upload button.
- **Root cause:** Upload errors shared the general editor error state and display.
- **Fix:** File size is checked as soon as files are selected. An oversized file clears the picker, disables Upload, and shows "*name* is larger than 25 MB. Upload a file smaller than 25 MB." in an alert directly under the upload control. Server-side upload errors (wrong type, 413) appear there too. The 25 MiB server limit is unchanged.
- **How it went:** Reported from manual use. Tests check both sides of the boundary: 25 MiB + 1 byte is rejected without an API call, and exactly 25 MiB is accepted.
- **Verification:** Three tests in `ReportEditorPage.test.tsx`.

### BUG-07 — Budget grid lost typing focus on every keystroke (Medium)

- **Fixed:** `cfaba72` (2026-10-14).
- **File:** `frontend/src/routes/ReportEditorPage.tsx`
- **Symptom:** Typing in a budget row's Category box lost focus after each character, so users had to click back in for every letter.
- **Root cause:** Each row's React key was `${index}-${line.category}`. Changing the category changed the key, so React destroyed and rebuilt the row on every keystroke.
- **Fix:** Rows now use a key that doesn't change as the user types (the row position).
- **How it went:** A one-line fix, but the cause isn't obvious from the symptom. A test was written first and confirmed to fail against the old key.
- **Verification:** `ReportEditorPage.test.tsx` focus-retention test.

### BUG-08 — Revision-request comment never shown to the submitter (Medium)

- **Fixed:** `cfaba72` (2026-10-14).
- **File:** `frontend/src/routes/ReportEditorPage.tsx`
- **Symptom:** When Council requested a revision, the submitter saw the status change but not the reviewer's comment explaining what to fix.
- **Root cause:** The comment was saved in the audit history, but the editor never read it.
- **Fix:** The editor finds the latest `REQUEST_REVISION` audit event and shows its comment and date in a banner at the top of the report.
- **How it went:** Simple fix; it completes the BR-019A revise-and-resubmit loop.
- **Verification:** Component test for the revision banner.

### BUG-09 — Demo seed had no report a submitter could start (Medium)

- **Fixed:** `5788584` (2026-10-13).
- **File:** `database/seed_demo.sql`
- **Symptom:** After loading the seed, no submitter had anything under "Available reports," even though the README promised an open unstarted assignment.
- **Root cause:** Every assignment in an open cycle already had a seeded submission, and the app correctly hides assignments that already have one.
- **Fix:** Added a Staten Island organization and submitter with an open, unstarted, intentionally overdue assignment. Also added incomplete and unbalanced drafts so triage has data to show.
- **How it went:** First flagged in the 2026-10-13 audit and fixed in the next pass. The README demo accounts were updated to match.
- **Verification:** Not run against MySQL; checked by reading the seed.

### BUG-10 — Budget validation API had no login check (Medium, security)

- **Fixed:** `e3eb3cc` (2026-10-13).
- **File:** `backend/app/routers/budgets.py`
- **Symptom:** `POST /api/budgets/validate` could be called without signing in, unlike every other report endpoint.
- **Root cause:** The route was written without the `get_current_user` dependency.
- **Fix:** Added `Depends(get_current_user)`.
- **How it went:** Low data exposure, because the endpoint only does arithmetic and reads no stored data. It was fixed anyway because the rules require authorization on every backend operation.
- **Verification:** Backend test suite.

### BUG-11 — Error messages shown as raw JSON (Medium)

- **Fixed:** `cfaba72` (2026-10-14).
- **File:** `frontend/src/api/client.ts`
- **Symptom:** Errors appeared as text like `{"detail":"Budget does not reconcile..."}` instead of a readable sentence, which went against BR-021's clear-error requirement.
- **Root cause:** The API client threw the raw response body.
- **Fix:** Added `errorMessageFrom`, which reads FastAPI's `detail` as a string or a list of validation messages and falls back to plain text.
- **Verification:** Tests in `client.test.ts`.

### BUG-12 — ORM missing database check constraints; Pydantic v2 not pinned (Medium)

- **Fixed:** `5788584` (2026-10-13).
- **Files:** `backend/app/models/__init__.py`, `requirements.txt`
- **Symptoms:**
  1. The SQLAlchemy models didn't declare four `CHECK` constraints that exist in the schema (initiative can't be its own predecessor, cycle start ≤ due date, budget line 1–100, attachment ≤ 25 MiB). The SQLite test databases therefore never enforced them.
  2. The code uses Pydantic v2 features, but `requirements.txt` didn't require v2, so a fresh install could pull an incompatible version.
- **Fix:** Declared the four constraints in the models (no database schema change) and added a direct `pydantic>=2` requirement.
- **Verification:** `test_model_contract.py`. SQLite still can't prove live MySQL matches.

### BUG-13 — Configuration split across two `.env` files; JSON header sent on GET requests (Medium)

- **Fixed:** `b1c6458` (2026-10-12).
- **Files:** `backend/app/core/config.py`, `frontend/vite.config.ts`, `frontend/src/api/client.ts`
- **Symptoms:**
  1. The backend read `backend/.env` and the frontend read `frontend/.env`, so settings could drift between them.
  2. Every request without a body (all GETs) was sent with `Content-Type: application/json`, which adds needless cross-origin preflight requests.
  3. Attachment downloads used their own `fetch` call that skipped the shared error handling.
- **Root causes:** Each side loaded `.env` from its own folder; `body !== null` is true when the body is `undefined`; the download helper was written separately.
- **Fix:** Both sides read a single root `.env` (`PROJECT_ROOT` in config, `envDir: '..'` in Vite). The JSON header is set only when there is a body. Downloads go through the shared request function with a blob response type.
- **Verification:** `client.test.ts`.

### BUG-14 — Printed reports lost table borders (Low)

- **Fixed:** `cfaba72` (2026-10-14).
- **File:** `frontend/src/index.css`
- **Symptom:** Printing or saving a report as PDF dropped the budget table's grid lines, which broke the "grid-accurate printable PDF" requirement.
- **Fix:** Print styles now force collapsed tables with a 1px border on every cell and stop rows from splitting across pages.
- **Verification:** Build only; checked visually by printing.

### BUG-15 — "Initiatives & forms" button invisible (Low)

- **Fixed:** `5788584` (2026-10-13).
- **File:** `frontend/tailwind.config.js`
- **Symptom:** The admin link on the review page showed white text on no background, so it was effectively invisible.
- **Root cause:** The page used `bg-brand-600` and `border-brand-300`, but those shades weren't defined in the Tailwind theme, so no CSS was generated for them.
- **Fix:** Added `brand.300` and `brand.600` to the theme.
- **Verification:** Build output contains the generated classes.

---

## Known open issues (not fixed)

| Issue | Why it is open |
| :--- | :--- |
| `HTTP_413_REQUEST_ENTITY_TOO_LARGE` deprecation warning | Kept on purpose: older Starlette versions allowed by `fastapi>=0.115` lack the new name. |
| `httpx` test-client deprecation warning | Comes from the installed library versions, not project code. |
| Registry imports, logins and permission changes not audit-logged | `audit_logs.submission_id` is required; needs an approved schema change. |
| Claude Code pre-commit hook sometimes triggers on non-commit commands | Affects agent tooling only, not the application. |

## Statistics

- **Bugs fixed:** 15 entries. BUG-12 and BUG-13 each group related defects, so 18 individual defects in total.
- **By priority:** 3 Critical, 3 High, 7 Medium, 2 Low.
- **By area:** 6 backend, 6 frontend, 2 database/seed, 1 configuration.
- **Security-related:** BUG-01, BUG-03, BUG-05, BUG-10.
- **Regression introduced and fixed within the period:** BUG-03 (added in `9beaee3`, removed in `5dbb6c1` the same day).
