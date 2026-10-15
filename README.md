# NYC Council Initiative Reporting System

Local demonstration for NYC Council Initiative Reporting System RFP PIN #102202709162026.

## Portals

- **External submitter:** organization-scoped assignments, autosaved drafts, dynamic questions, a 1–100 row budget grid with budgeted and actual amounts, allowlisted supporting uploads, submission history, and printable receipts.
- **Council Finance:** searchable submission and incomplete-report queues, open-obligation triage, review dispositions, version and audit history, analytics, CSV/XLSX exports, and print-ready report views.
- **Council administrator:** user role and active-state management, password resets, initiative/cycle/organization assignment and versioned form configuration, plus annual rollover with lineage.

The local demo logs submission confirmation metadata to the backend console. It does not send email. The print views can be saved as PDF through the browser's print dialog. XLSX export uses pandas and openpyxl from `requirements.txt`.

## Screenshots

All data shown is synthetic demo data from `database/seed_demo.sql`.

### Sign in

![Sign in page](reference_images/login.png)

- Choose a portal: **External Submitter** or **Council Finance**.
- Sign in with an individual email and password (no shared accounts). Passwords are checked against bcrypt hashes in MySQL.
- The account's role is loaded from the database. Choosing a portal that doesn't match the role leads to an access-denied page.
- Login errors from the server are shown as plain messages.

### Submitter dashboard

![Submitter dashboard](reference_images/external_submitter_dashboard.png)

- Summary cards: linked organizations, new report assignments, drafts or updates needed, and submitted reports.
- **My reports** lists every report for the user's organizations, including reports started by colleagues, with initiative, organization, cycle, status and budget total.
- **Continue report** reopens a draft or a report returned with **REVISION_REQUESTED**.
- **Available reports** lists open cycles the organization is assigned to (by EIN) that have a published form, and starts a new report. Only one report can exist per organization, initiative and cycle.
- Users only ever see their own organizations; the backend enforces this on every request.
- Collapsible sidebar that remembers its state, with the signed-in user, role and **Log out**.

### Report editor

![Report editor](reference_images/external_submitter_report.png)

- **Step 1 · Report questions:** questions come from the initiative's published form version. Supports text, narrative, number, currency, percentage, date, dropdown and yes/no fields, required fields, character and word limits, and questions that only appear based on an earlier answer.
- **Step 2 · Budget grid:** 1–100 lines with category, description, budgeted amount and actual amount. Add or remove lines; the live total, actual total and variance update as you type.
- **Step 3 · Supporting documents:** upload several files (PDF, Excel, Word, CSV and other allowed types), each up to 25 MiB. Oversized files are rejected immediately with a message under the upload button. Each file's type, size and SHA-256 checksum are recorded.
- **Step 4 · Review and submit:** shows report ID, status, computed total and the configured balance check.
- **Autosave** keeps drafts safe while editing; **Save draft** saves manually so work can be resumed later.
- **Submit report** runs server-side validation (required fields, data types, limits, budget must match the configured total). Errors are listed in plain language and the report is not submitted until they are fixed.
- When Council requests a revision, the reviewer's comment is shown at the top, and the report can be edited and resubmitted. Every submission is saved as a new version.
- After submission, the report can be printed or saved as PDF.

### Submission oversight (Council Finance)

![Submission oversight](reference_images/council_admin_submission_oversight.png)

- Totals for submitted reports, reported budget, allocated budget and balanced reports.
- Charts for submission counts by status and reported budget by borough.
- **Open reporting obligations:** assigned organizations that haven't started a report for an open cycle, with due date, overdue flag and awarded amount.
- Search and filter by initiative, organization, cycle, ID, EIN, borough, fiscal year, reporting cycle, status, or **Unbalanced only**.
- The submission list flags unbalanced budgets, incomplete drafts and validation errors.
- **Download Excel** (`.xlsx`) and **Download CSV bundle** (zip) export all submissions, budget lines and attachment details. Cell values that look like spreadsheet formulas are neutralized.
- Opening a submission shows its answers, budget, attachments (authorized download), version history and audit history. Reviewers can start review, request a revision, approve or reject with a comment. Administrators can edit a submitted report; each edit is saved as a new version and logged. Each report can be printed or saved as PDF.
- View-only users can see everything here but cannot take review actions.

### User administration (Council administrators)

![User administration](reference_images/council_admin_user_admin.png)

- **Create user account** with full name, email, initial password (12–72 characters) and role: Council administrator, Council reviewer, view only, or external submitter.
- External submitters must be linked to at least one active organization; other roles can't be.
- Change a user's role, active status and organizations, and reset passwords. The last active administrator can't be removed or demoted, and administrators can't demote themselves.
- **Add organization to EIN registry** with EIN, legal name, organization type (CBO or city agency) and borough. Duplicate EINs are rejected.
- **Import authoritative EIN registry** from a CSV file (`ein`, `legal_name`, optional `org_type`, `borough`, `status`). Every row is checked first; if any row is invalid, nothing is imported. Organizations missing from the file are reported, not removed.

### Initiatives & forms (Council administrators)

![Initiatives and forms](reference_images/council_admin_initiatives%26forms.png)

- **Create initiative** with a unique code, name and fiscal year. Each initiative's status can be set to active, combined or retired, and its predecessor/successor lineage is shown.
- **Configure initiative:** choose an initiative to manage its cycles, assignments, form versions and lineage.
- **Add reporting cycle** with name, start date, due date and status (upcoming, open, closed).
- **Assign organization** by EIN with an awarded amount. The EIN is checked against the registry as you type and the organization's details are filled in. Assignment is only allowed for active registry organizations.
- **Create form version** from a JSON definition: sections, field types, required fields, limits, dropdown options, conditional questions (`visible_when`) and the budget balance rule. Definitions are validated before saving. Published versions are never edited; changes create a new version.

### Annual rollover (Council administrators)

![Annual rollover](reference_images/council_admin_annual_rollover.png)

- Copy every active initiative from a source fiscal year into a new fiscal year in one step.
- Copies organization assignments and awarded amounts, reporting cycles (dates moved forward, status set to upcoming) and form versions.
- Each new initiative is linked to the one it came from, so history carries across years. Source-year data is not changed.
- The destination year must be later than the source year; conflicts with existing records are rejected without partial changes.

See [application requirements](.claude/rules/02-business-rules.md) for the portal workflows and reporting capabilities. See [ProductionUpdate.md](ProductionUpdate.md) for technology changes needed to move the local stack to production.

## Requirements

- MySQL 8.0+
- Python 3.11+
- Node.js and npm

## Local database setup

`database/schema.sql` contains the project schema contract. `database/seed_demo.sql` adds synthetic users, organizations, assignments, form templates, and workflow examples. Use these only in a local demo database. The seed is intended to run once against an empty schema.

To rebuild the local demo database, open a terminal at the cloned repository root and connect to your local MySQL instance. The `SOURCE` paths below are relative to that directory. Confirm that you are connected to the local demo server before dropping anything.

```powershell
mysql -u root -p
```

At the MySQL prompt, run:

```sql
DROP DATABASE IF EXISTS council_irs_db;
SOURCE database/schema.sql;
SOURCE database/seed_demo.sql;
```

These steps erase all data in `council_irs_db`. Never run the reset against a shared, staging, or production database. The application does not create or migrate schema on startup.

### Demo accounts

All accounts are synthetic and use demo-only passwords. Change or remove them before exposing the application beyond a local interview/demo environment.

| Role | Email | Password |
| --- | --- | --- |
| Council administrator | `admin@council.nyc.gov` | `admin123` |
| Council reviewer | `reviewer@council.nyc.gov` | `review123` |
| View only | `viewer@council.nyc.gov` | `review123` |
| Harlem submitter | `submitter.harlem@cbo.org` | `test123` |
| Queens submitter | `submitter.queens@cbo.org` | `test123` |
| City agency submitter | `submitter.agency@nyc.gov` | `test123` |
| Bronx submitter | `submitter.bronx@cbo.org` | `test123` |
| Brooklyn submitter | `submitter.brooklyn@cbo.org` | `test123` |
| Staten Island submitter | `submitter.statenisland@cbo.org` | `test123` |

The synthetic records cover two incomplete, unbalanced drafts (one has a zero-value budget row); a flagged submitted report with a budget shortfall; a balanced submitted report; a report in review; a revision-requested report; an approved report; and an open unstarted report. The unstarted assignment is intentionally overdue while still open, so Council users can exercise overdue triage and the submitter can start and complete it. The flagged submitted case is intentionally seeded for reviewer triage; new submissions still go through server-side budget validation. Upload documents through the portal; they are stored under the repository-root `.uploads/` directory, which is ignored by Git and starts empty.

## Backend

Copy the single root `.env.example` to `.env`. Set `DATABASE_URL` for the local MySQL database and replace `SECRET_KEY` with a unique local-only random value. The same file configures the frontend API URL; `.env` is ignored by Git and must never be committed.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Verification

```powershell
python -m compileall -q backend/app
python -m pytest backend/tests -q

cd frontend
npm run lint
npm test
npm run build
```

When using Claude Code 2.1.295 or later, `.claude/settings.json` registers pre-commit checks for Bash and PowerShell `git commit` commands. A failed check blocks the commit.

## Project references

- [Application business rules](.claude/rules/02-business-rules.md), [architecture/scope](.claude/rules/01-architecture.md), and [database contract](.claude/rules/04-database-contract.md)
- [Database schema](database/schema.sql) and [synthetic demo seed](database/seed_demo.sql)
