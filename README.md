# SkillBridge Marketplace

CS 701 implementation of the SkillBridge independent service provider marketplace. This repository converts the approved CS 700 DFDs, ERD, application design, and security design into a runnable academic prototype.

## Current checkpoint scope

- Three roles: customer, provider, administrator
- Provider profiles, credentials, service packages, and publication approval
- Customer discovery and booking persistence
- Booking milestones and simulated transaction ledger
- Database constraints derived from BR-01 through BR-15
- Seeded demonstration records and acceptance tests
- Registration, login, password hashing, and bearer-token authentication
- Customer, provider, and administrator route protection
- Provider profile submission and administrator approval

The application does not collect, hold, or transfer real funds. All charges, commissions, and payouts are simulated ledger records.

## Stack

- React, TypeScript, and Vite client
- Python FastAPI API
- PostgreSQL database
- SQLAlchemy and Alembic migrations
- pytest API and business-rule tests
- Docker Compose local environment

## Local setup with Docker Desktop

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Open the API documentation at `http://localhost:8000/docs`.
4. Open the client at `http://localhost:5173`.

The API container applies the migration and loads seed data during startup.

## Run backend without Docker

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Tests

```powershell
cd backend
pytest
```

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Customer | `jordan.customer@example.test` | `Customer123!` |
| Provider | `maya.provider@example.test` | `Provider123!` |
| Administrator | `admin@skillbridge.test` | `Admin123!` |

These accounts are for local demonstrations only. Change `JWT_SECRET` before using the application outside the local course environment.

## Authentication and approval endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET` and `PUT /providers/me`
- `POST /providers/me/credentials`
- `GET /admin/providers/pending`
- `POST /admin/providers/{provider_id}/decision`

## Design traceability

See `docs/design-traceability.md`, `docs/database-model.md`, `docs/checkpoint-acceptance.md`, `docs/migrations-and-seed-data.md`, `docs/authentication-and-roles.md`, `docs/provider-approval-workflow.md`, and `docs/checkpoint-demo-script.md`.
