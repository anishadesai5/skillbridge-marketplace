# Booking state and milestone workflow

This document records the implementation for Project Plan Tasks 10.1 and 10.2 (October 9-14, 2026) and the related Task 11 verification (October 14-16, 2026).

## Booking state rules

| Current state | Allowed next state | Authorized role |
|---|---|---|
| Pending | Confirmed | Assigned provider |
| Pending | Cancelled | Booking customer |
| Confirmed | Active | Assigned provider |
| Confirmed | Cancelled | Booking customer |
| Active | Completed | Assigned provider |
| Active | Cancelled | Booking customer |
| Completed | None | Terminal state |
| Cancelled | None | Terminal state |

The API rejects skipped, repeated, reversed, and post-terminal transitions. A booking cannot move to Active until it has a valid milestone plan. It cannot move to Completed until every milestone is Approved.

## Milestone persistence rules

- Only the assigned provider can save milestones.
- Milestones can be created or replaced only while a booking is Pending or Confirmed.
- Each milestone has a positive sequence number unique within its booking.
- Each allocation is greater than zero and no more than 100 percent.
- A batch must contain between 1 and 20 milestones.
- Allocations in the complete batch must total exactly 100.00 percent.
- Invalid batches are rejected before any partial milestone data is saved.

Example request for `PUT /bookings/{booking_id}/milestones`:

```json
{
  "milestones": [
    {
      "sequence": 1,
      "description": "Research and requirements",
      "allocation_pct": "40.00"
    },
    {
      "sequence": 2,
      "description": "Final delivery",
      "allocation_pct": "60.00"
    }
  ]
}
```

## API operations

| Method and route | Purpose |
|---|---|
| `GET /bookings/{booking_id}` | Return an authorized booking with its persisted milestones |
| `PATCH /bookings/{booking_id}/status` | Apply a validated booking-state transition |
| `PUT /bookings/{booking_id}/milestones` | Atomically replace the booking's milestone plan |

## Task 11 verification

Automated tests cover valid and invalid status changes, customer and provider permissions, milestone persistence, duplicate sequences, incorrect allocation totals, the start prerequisite, and the completion prerequisite. The database migration is also applied to a clean database, and the client production build is run as part of checkpoint verification.
