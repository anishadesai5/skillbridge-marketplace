# Provider availability and booking responses

Task 16 adds a provider calendar, booking conflict validation, and a provider response workflow.

## Availability rules

- A provider can block or reopen a future date from the provider workspace.
- An explicit unavailable calendar entry prevents customers from requesting that date.
- A provider can have only one nonterminal booking request on a date.
- Cancelled and Rejected requests no longer reserve the date.
- Availability records are unique by provider and date.

## Provider response rules

- Providers can retrieve only their own booking requests.
- A Pending request can be accepted or rejected by its assigned provider.
- Acceptance changes the status from Pending to Confirmed.
- Rejection changes the status from Pending to Rejected and requires a reason.
- Rejected is a terminal status and cannot be changed later.
- The response note and timestamp are saved with the booking.

## Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /providers/me/availability` | List future provider calendar entries |
| `PUT /providers/me/availability` | Block or reopen a provider date |
| `GET /providers/me/bookings` | List assigned booking requests |
| `POST /providers/me/bookings/{booking_id}/response` | Accept or reject a Pending request |

## Frontend demonstration

Sign in as the seeded provider to open the Provider Workspace. The page shows booking requests with Accept and Reject actions and a form for blocking future dates. A customer who requests a blocked or already reserved date receives a clear conflict message.

## Verification

Automated tests cover unavailable dates, duplicate date conflicts, provider inbox access, acceptance, required rejection reasons, date release after rejection, and cross-provider authorization. The complete backend regression suite and React production build are run before submission.
