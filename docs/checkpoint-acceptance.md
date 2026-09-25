# October 17 checkpoint acceptance scenarios

## AC-01 Repeatable local setup

Given Docker Desktop and the repository, when `docker compose up --build` completes, PostgreSQL, the API, and the client are available without manual database creation.

## AC-02 Seeded roles

The seed command creates a customer, provider, and administrator. Each account has exactly one role and the API rejects access outside that role.

## AC-03 Provider publication gate

A provider begins unpublished. The provider cannot publish until an administrator verifies at least one credential.

## AC-04 Service packages

A verified provider can create a positive-price service package. A customer can retrieve published providers and their active packages.

## AC-05 Booking persistence

A customer can request an active package for a future date. The database stores customer, provider, package, total, date, and Pending status.

## AC-06 Milestone allocation

A booking with milestones is valid only when allocations total 100 percent. Each milestone sequence is unique inside that booking.

## AC-07 Role protection

Customer APIs cannot modify provider or administrator data. Provider APIs cannot read another provider's private data. Administrator APIs require the administrator role.

## AC-08 Simulated payment boundary

No endpoint accepts card or bank information. Any amount shown as charged, held, commission, or payout comes from a simulated ledger row.

## AC-09 Database integrity

Automated tests reject invalid rating, price, commission, and financial reconciliation values.

## AC-10 Evidence

The checkpoint demonstration shows database migrations, seeded rows, Swagger documentation, provider listing, and a persisted booking request.
