# Migrations and Seed Data

## Apply the schema

From the `backend` directory:

```powershell
alembic upgrade head
python -m app.seed
```

The initial Alembic revision creates the SkillBridge tables and the constraints defined by the SQLAlchemy model. Important constraints include unique account email addresses, positive service prices and booking totals, provider ratings between zero and five, unique milestone sequence numbers per booking, milestone allocation limits, commission limits, and ledger reconciliation.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Customer | `jordan.customer@example.test` | `Customer123!` |
| Provider | `maya.provider@example.test` | `Provider123!` |
| Administrator | `admin@skillbridge.test` | `Admin123!` |

These credentials are only for the local academic demonstration. The seed process stores password hashes, not plaintext passwords.

The seeded provider has a verified portfolio credential and two design service packages. Running the seed command again does not duplicate the demonstration records.
