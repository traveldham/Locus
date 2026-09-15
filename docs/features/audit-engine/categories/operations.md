# Operations worker

Category `operations`, weight 15. Module: `backend/app/services/recommendations/categories/operations.py`.
Suggestion layer: `backend/app/services/recommendations/suggestions/operations.py`.
Research and thresholds: `docs/features/audit-engine/research/06-operations-worker.md`.

## What it answers

Do appointment requests become visits? Four groups of checks over the booking system's
requests (`bookings`), the profile's hours, the project's service list and Google's
daily bookings count. Every check is deterministic. A permanently closed profile
suppresses every check; a profile with no requests in the window abstains on every check.

All request-level checks use requests made in the last `booking_window_days` (90),
by `booking_created_at`. Statuses are current state and often stale, so a future visit
is never a failure and outcome rates use only settled statuses as their denominator.

| Group | Rule | Weight | Severity | Fails when | Abstains when |
| --- | --- | --- | --- | --- | --- |
| Response | `requests_unanswered` | 3 | warning to critical by age | a request is still `new` more than `booking_wait_days` (3) after it was made; one finding per request, subject is the booking reference | no requests in the window |
| Response | `requests_expired` | 2 | warning | `new` requests whose requested date has passed | no requests in the window |
| Response | `confirmation_rate_low` | 2 | warning to critical | confirmed + completed + no-show share of requests older than the wait below `booking_confirmation_min` (0.7) | fewer than `booking_min_requests` (10) decidable requests |
| Outcomes | `cancellation_rate_high` | 2 | warning to critical | cancelled share of settled visits (completed, cancelled, no-show) above `booking_cancellation_max` (0.2) | fewer than `booking_min_settled` (10) settled visits |
| Outcomes | `no_show_rate_high` | 2 | warning to critical | no-show share of settled visits above `booking_no_show_max` (0.1) | fewer than `booking_min_settled` settled visits |
| Demand | `service_not_listed` | 1 | notice | a requested service matches no project service by name or shared word; one finding per service | no project services, or no request names a service |
| Demand | `weekend_demand_without_hours` | 2 | warning | at least `booking_weekend_min_requests` (5) requests for a Saturday or Sunday with no regular hours for that day; one finding per day | no regular hours stored (open days unknown); passes when weekend demand is below the floor |
| Demand | `lead_time_shrinking` | 1 | notice | median lead time (requested date minus request date) in the last `booking_lead_recent_days` (28) below `booking_lead_collapse_ratio` (0.5) of the earlier median | fewer than `booking_min_requests` in either slice |
| Tracking | `channel_concentrated` | 1 | notice | one channel carries more than `booking_channel_share_max` (0.9) of requests with a channel | fewer than `booking_min_requests` with a channel |
| Tracking | `google_bookings_untracked` | 1 | notice | Google's daily `bookings` sums to zero across the window while requests exist | no day in the window reports the metric |

Semantics that matter:

- A `new` request is stale by the age of the request, never by the date of the visit.
- `confirmed` for a past date is not a failure and not a settled outcome; it is a visit
  whose result was never recorded, and it is left out of every rate.
- Cancelled counts against confirmation even when the customer cancelled.
- `null` from Google is unknown, not zero. CRM requests and Google's bookings count are
  separate measurements and never reconciled.
- `customer_name` is stripped before the snapshot is written. Findings identify a
  request by `external_booking_id` only.
- Every threshold is a field on `EngineConfig` under `# ---- operations worker ----`.

## Card

`card(snapshot)` returns the request funnel for the operations tab: counts by status in
the window, confirmation, cancellation and no-show rates, settled count, median lead
days, the age of the oldest waiting request, weekend request count, top services
requested and the channel mix. A card is handed no analysis date, so the newest request
date stands in for it and is returned as `as_of`.

Frontend: `frontend/src/components/recommendations/cards/operations-card.tsx` exports
`OperationsCard` (typed to `CategoryCardProps`). It shows the funnel as horizontal
bars, three rate tiles, lead time, oldest waiting request, services and channel bars,
and the first drafted follow-up message when a finding carries one. Registering it in
`cards/registry.ts` is a separate step.

## Suggestions

After the checks run, the worker task calls the suggestion layer, which asks the
configured model for one draft per finding whose check declares a `suggests` field:

| Check | Field drafted | Shape |
| --- | --- | --- |
| `requests_unanswered` (the oldest 10 at most) | `followup_message` | text under 300 characters, names the service, asks the customer to confirm a time; no name, phone, email, URL or price |
| `no_show_rate_high` | `reminder_plan` | list of 3 to 5 concrete steps |
| `weekend_demand_without_hours` | `hours_note` | text under 400 characters for the manager |

The prompt carries the business, its regular hours, anonymised booking statistics
(counts by status, services, channels, median lead time), the project's service list and
projects. No customer identity is available to it. The response is constrained by a
JSON schema, and code enforces the rest: a draft with a URL, an email, a phone number
or a greeting followed by a name is dropped; text is trimmed to its cap on a word; a
reminder plan with fewer than three clean steps is dropped and one with more than five
is cut; one draft per finding.

`fallback_summary` is deterministic and used when no model answered.

## Tests

- `backend/tests/test_operations_worker.py`: every check declared and assessed once, a
  healthy location scores 100, closed suppresses, no requests abstains, one mutation
  per check flips its verdict or abstains, and the card never carries a name.
- `backend/tests/test_operations_suggestions.py`: target selection and the follow-up
  cap, anonymised context and prompt, attachment and validation of drafts, drops for
  names and contact details, failure recorded without losing findings, skip conditions.

## Not built yet

Response time for answered requests (no confirmation timestamp), reminder practice (no
reminder log), utilisation (no slot capacity), cancellation reasons.
