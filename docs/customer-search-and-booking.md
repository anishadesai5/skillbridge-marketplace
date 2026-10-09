# Customer Search and Booking — Task 9

## Implemented customer flow

1. A visitor searches active packages from approved, published providers.
2. The visitor filters by keyword, category, price range, and provider rating.
3. The visitor opens a provider detail view and reviews active packages.
4. A signed-in customer selects a date and submits optional requirements.
5. The API derives the customer from the bearer token and the total from the stored package price.
6. PostgreSQL persists the request with `Pending` status and a simulated payment hold.
7. The customer can retrieve the request from **My Bookings**.

## Endpoints

- `GET /services?q=&category=&min_price=&max_price=&min_rating=`
- `GET /providers/{provider_id}`
- `POST /bookings` (customer token required)
- `GET /customers/me/bookings` (customer token required)

Example booking request:

```json
{
  "package_id": 1,
  "booking_date": "2026-10-15",
  "customer_notes": "Please focus on keyboard navigation."
}
```

The client does not submit `customer_id` or `total`. This prevents a customer from booking on behalf of another account or changing the package price.

## Acceptance checks

- Pending/unpublished providers and inactive packages do not appear publicly.
- Reversed price ranges return `422`.
- Missing providers and packages return `404`.
- Past booking dates return `422`.
- Provider and administrator accounts receive `403` on customer booking routes.
- Newly created requests appear in the authenticated customer's booking list.
- All payment behavior remains simulated; the application stores no card or bank information.

## Demo sequence

1. Run `docker compose up --build`.
2. Register a local customer account from the application and sign in.
3. Filter for Design services between $100 and $500.
4. Open Maya Patel's provider detail.
5. Select a future date, add a note, and request the Accessibility UX Review.
6. Show the success message and the new Pending row under **My Bookings**.
7. Optionally open `/docs` and run `GET /customers/me/bookings` with the same bearer token.
