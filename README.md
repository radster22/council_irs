# NYC Council Initiative Reporting System

Local demonstration for NYC Council Initiative Reporting System RFP PIN #102202709162026.

## Portals

- **External submitter:** organization-scoped assignments, draft reports, dynamic questions, budget lines, supporting uploads, and submission history.
- **Council Finance:** searchable review queue, report detail, review dispositions, audit history, and admin-only user listing.

Form administration, annual rollover, spreadsheet/PDF exports, email delivery, and production operations are not implemented in this local demo. See [ProductionUpdate.md](ProductionUpdate.md) for deferred production work and [business_rules/COMPLIANCE_DIAGNOSTIC.md](business_rules/COMPLIANCE_DIAGNOSTIC.md) for the current rule assessment.

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

The synthetic records cover two unbalanced cases (a draft and a flagged submitted report), a balanced submitted report, a report in review, a revision-requested report, an approved report, and an open unstarted assignment. The flagged submitted case is intentionally seeded for reviewer triage; new submissions still go through server-side budget validation. Upload a real local file through the portal to demonstrate attachments; the seed does not create pretend file metadata.

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

## Project references

- [Functional requirements](context/rfp-functional-specs.md) and [schema reference](context/db-schema-reference.md)
- [Database schema](database/schema.sql) and [synthetic demo seed](database/seed_demo.sql)
- Source RFP, proposed architecture, and business-rules workbook: `business_rules/`
