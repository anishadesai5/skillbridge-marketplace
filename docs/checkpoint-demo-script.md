# October 17 Checkpoint Demo Script

## Preparation

1. Copy `.env.example` to `.env` and replace `JWT_SECRET` with a local random value.
2. Run `docker compose up --build`.
3. Confirm `http://localhost:8000/health` returns `database: connected`.
4. Open `http://localhost:8000/docs` and `http://localhost:5173`.
5. Run `pytest` from the backend directory and capture the passing result.

## Demonstration

1. Sign in as the seeded customer and show the customer workspace.
2. Browse the published provider and two seeded service packages.
3. Create a new provider account and show its pending status.
4. Update the new provider profile and submit a credential.
5. Attempt an administrator route with the provider token and show the `403` response.
6. Sign in as the administrator and list pending providers.
7. Approve the new provider and confirm that the profile becomes published.
8. Return to provider discovery and show the approved provider.
9. Create a customer booking and show the simulated payment hold.

## Evidence to retain

- Passing test output
- Swagger authentication and role-protection responses
- Registration and login screens
- Pending and approved provider responses
- Database rows for the three account roles
- Git commit used for the demonstration
