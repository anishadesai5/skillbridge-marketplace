# Authentication and Roles

SkillBridge uses bearer tokens signed with HS256. Passwords are hashed with Argon2 through `pwdlib`. The token contains the account identifier, role, issue time, and expiration time.

Set `JWT_SECRET` to a long random value outside source control before any non-demo deployment.

## Authentication endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register a customer or provider and return an access token |
| POST | `/auth/login` | Validate credentials and return an access token |
| GET | `/auth/me` | Return the authenticated account |

Public registration does not permit administrator accounts. The seed command creates the demonstration administrator.

## Role permissions

| Capability | Customer | Provider | Administrator |
|---|---:|---:|---:|
| Browse published providers | Yes | Yes | Yes |
| Create own booking | Yes | No | No |
| Update own provider profile | No | Yes | No |
| Submit provider credential | No | Yes | No |
| View pending providers | No | No | Yes |
| Approve or reject providers | No | No | Yes |

The backend enforces these permissions. The client also adjusts the visible workspace and disables customer booking actions for other roles.
