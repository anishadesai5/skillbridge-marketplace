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
- Searchable service listings with category, price, rating, and keyword filters
- Approved provider detail pages and active package display
- Authenticated booking requests with server-calculated pricing
- Customer booking history with persisted Pending status
- Validated booking lifecycle from Pending through Completed or Cancelled
- Provider-defined milestones with unique sequences and exact 100% allocation
- Provider availability calendar and booking conflict prevention
- Provider booking inbox with accept and reject responses
- Provider milestone submission and resubmission after customer revision requests
- Idempotent customer approval with reconciled simulated commission and payout records

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

## Seeded demonstration data

| Role | Email |
|---|---|
| Customer | `jordan.customer@example.test` |
| Provider | `maya.provider@example.test` |
| Administrator | `admin@skillbridge.test` |

Seeded accounts use generated passwords so credentials are never committed. For the customer booking demo, create a customer account from the registration screen. Change `JWT_SECRET` before using the application outside the local course environment.

## Authentication and approval endpoints

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET` and `PUT /providers/me`
- `POST /providers/me/credentials`
- `GET /admin/providers/pending`
- `POST /admin/providers/{provider_id}/decision`

## Customer search and booking endpoints

- `GET /services`
- `GET /providers/{provider_id}`
- `POST /bookings` (customer only)
- `GET /customers/me/bookings` (customer only)

## Booking state and milestone endpoints

- `GET /bookings/{booking_id}` (booking customer, provider, or administrator)
- `PATCH /bookings/{booking_id}/status` (authorized customer or provider)
- `PUT /bookings/{booking_id}/milestones` (assigned provider only)

The normal lifecycle is `Pending -> Confirmed -> Active -> Completed`. A customer may cancel an eligible booking, and the assigned provider may reject a Pending request. Completed, Cancelled, and Rejected are terminal states. Milestone allocations must total exactly 100 percent before work can start, and every milestone must be approved before a booking can be completed.

## Provider availability and response endpoints

- `GET /providers/me/availability`
- `PUT /providers/me/availability`
- `GET /providers/me/bookings`
- `POST /providers/me/bookings/{booking_id}/response`

Providers can block or reopen future dates from the React workspace. Booking creation rejects explicitly unavailable dates and dates already reserved by a nonterminal request. Providers can accept a Pending request, which moves it to Confirmed, or reject it with a required reason. Rejected and Cancelled requests release the date for a new request.

## Milestone submission, revision, and approval endpoints

- `POST /bookings/{booking_id}/milestones/{milestone_id}/submit` (assigned provider)
- `POST /bookings/{booking_id}/milestones/{milestone_id}/revision` (booking customer)
- `POST /bookings/{booking_id}/milestones/{milestone_id}/approve` (booking customer)

Providers may submit pending work and resubmit work after a revision request. Customers may request a revision only while work is submitted. Approval is idempotent: repeating the request returns the original simulated ledger release instead of creating a duplicate. The release amount is the booking total multiplied by the milestone allocation; the prototype records a 10% simulated commission and a payout equal to the release minus commission.

## Design traceability

See `docs/design-traceability.md`, `docs/database-model.md`, `docs/checkpoint-acceptance.md`, `docs/migrations-and-seed-data.md`, `docs/authentication-and-roles.md`, `docs/provider-approval-workflow.md`, `docs/customer-search-and-booking.md`, `docs/booking-state-and-milestones.md`, `docs/provider-availability-and-responses.md`, and `docs/checkpoint-demo-script.md`.
