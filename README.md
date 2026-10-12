# NYC Council Reporting

Starter repository for a New York City Council budget reporting system.

## Structure

- `backend/`: FastAPI service and tests.
- `frontend/`: frontend source organization and package manifest.
- `database/`: reserved for schema artifacts; the live database is authoritative and no seed data is required.
- `context/`: requirements and architecture references.
- `examples/`: representative JSON payloads.
- `.uploads/`: local-only upload directory; contents are ignored by Git.

## Backend

Copy `backend/.env.example` to `backend/.env` and configure the local MySQL URL and a random JWT secret. The local `.env` file is ignored by Git; URL-encode reserved characters in database passwords.

```powershell
cd C:\Repos\council_irs
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

The frontend is a Vite, React 18, TypeScript, React Router, and Tailwind CSS application.

```powershell
cd C:\Repos\council_irs\frontend
npm install
npm run dev
```

Run `npm run lint` for TypeScript checking and `npm run build` for the production build. A frontend test runner and `npm test` script are not configured yet.

## Source Documents

The supplied RFP, proposed architecture, and user stories/business rules are in `business_rules/`. See `context/rfp-functional-specs.md` for the requirement hierarchy and confirmed functional summary, and `business_rules/COMPLIANCE_DIAGNOSTIC.md` for the current rule-by-rule code assessment.
