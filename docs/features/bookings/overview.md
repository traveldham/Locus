# Bookings

Appointment requests from the customer's own booking system or CRM. **Never from Google**,
and read-only in this build.

Code: `app/api/bookings.py`, `app/models/bookings.py`, schemas in
`app/schemas/performance.py`. Screen: `frontend/src/components/bookings/`.

## Why they are `source = locus`, permanently

Google's performance API reports a **bookings count** attributed to the profile and nothing
else — no customer, no service, no status, no cancellation. Individual records like these can
only come from the system that actually took the appointment.

So `performance_daily.bookings` and the `bookings` table are two different measurements of
loosely related things, and **they will not agree**. There is no join, no foreign key and no
reconciliation code between them. The provenance mark is what makes that legible instead of
alarming.

## The one endpoint

```
GET /api/v1/bookings
    ?location_id=  &project_id=  &status=  &booking_source=  &limit=  &offset=
```

`limit` 1-200, default 50. Ordering is `requested_for_date DESC NULLS LAST, id`.

`status_counts` is computed **before** the `status` filter is applied, so selecting one status
does not empty the summary strip above the table.

`serialize` overwrites `created_at` with `booking_created_at` after validation, because
`from_attributes` would otherwise fill it from `TimestampMixin.created_at` — our row-write
time, not the customer's request time.

## The model

`bookings`, unique on `(location_id, external_booking_id)`, indexed on
`(location_id, requested_for_date)`.

```python
class BookingStatus(StrEnum):
    new = "new"; confirmed = "confirmed"; completed = "completed"
    cancelled = "cancelled"; no_show = "no_show"

class BookingChannel(StrEnum):
    website = "website"; google_profile = "google_profile"
    phone = "phone"; walk_in = "walk_in"
```

### `booking_source` vs `source`

Two different questions, which is why the column is not simply called `source`:

| Column | Answers |
| --- | --- |
| `booking_source: BookingChannel` | **How the customer reached us** — website, Google profile, phone, walk-in |
| `source: DataSource` | **Where the row itself came from** — always `locus` |

`customer_name` is stored but **stripped before the audit snapshot is written**, so no
finding ever names a person; a request is identified by `external_booking_id` only.

## What the audit does with them

Ten checks in the operations worker, over requests created in the last 90 days. The semantics
that trip people up:

- A `new` request is stale by the **age of the request**, never by the date of the visit.
- `confirmed` for a past date is not a failure and not a settled outcome — it is a visit whose
  result was never recorded, and it is left out of every rate.
- Outcome rates use only **settled** statuses (`completed`, `cancelled`, `no_show`) as their
  denominator, so a future visit can never count against the business.
- Cancelled counts against the confirmation rate even when the customer cancelled.
- Small denominators abstain: fewer than 10 decidable requests, or 10 settled visits, and the
  rate checks return `insufficient_data` rather than a number.

See [../audit-engine/categories/operations.md](../audit-engine/categories/operations.md).

## Known gap

The backend returns `status_counts` on the list envelope, but the TypeScript type omits it and
no component reads it — the view derives its figures from a second count query instead.
