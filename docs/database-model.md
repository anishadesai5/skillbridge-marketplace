# Database model

The migrations implement the CS 700 ERD and the approved CS 701 scheduling extension.

| Entity | Primary key | Main relationships |
| --- | --- | --- |
| UserAccount | id | Shared authenticated identity and role |
| Provider | id | One user, many credentials and packages |
| ProviderAvailability | id | One provider and one unique calendar date |
| Credential | id | Belongs to provider |
| ServicePackage | id | Belongs to provider |
| Customer | id | One user, many bookings |
| Booking | id | Customer, provider, package |
| Milestone | id | Belongs to booking; sequence unique within booking |
| LedgerTransaction | id | Booking and optional milestone; simulated only |
| Dispute | id | Belongs to milestone; optional resolving administrator |
| Administrator | id | One user, commission rules and audit events |
| CommissionRule | id | Created by administrator; effective-dated |
| AdminAuditLog | id | Immutable administrator action record |

## Enforced constraints

- Ratings remain between 0 and 5.
- Package prices and booking totals are positive.
- Milestone allocations remain greater than 0 and at most 100 individually; the service validates that a booking totals 100 percent.
- Transaction amounts are nonnegative and payout equals amount minus commission.
- Commission rates remain greater than 0 and less than 100.
- Provider and customer emails are unique through the shared user account.
- Milestone sequence is unique within a booking.
- Provider availability is unique by provider and date.
- State transition, provider publication, dispute eligibility, allocation total, and ledger idempotency rules are service-layer checks because they depend on multiple rows or prior state.
