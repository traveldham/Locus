# Operations worker research

Status: 2026-09-14. Grounds the checks in `categories/operations.py`.

## What an operations audit of a clinic or local business looks at

The operations category is about what happens after a customer decides to book: how
fast the request is answered, how many requests become visits, how many visits are lost
to cancellations and no-shows, and whether the schedule the business offers matches
when customers actually want to come. None of it is a Google ranking factor. It is
where profile traffic turns into revenue, and it is the part of the funnel the business
controls entirely.

| Question | What the literature says | Source |
| --- | --- | --- |
| How fast must a request be answered? | Leads answered within an hour are about seven times more likely to be qualified than those answered an hour later; after 24 hours the chance falls off sharply. Google's own historical chat guidance was "reply within 24 hours" or the chat button is removed. | Harvard Business Review, "The Short Life of Online Sales Leads" (2011), https://hbr.org/2011/03/the-short-life-of-online-sales-leads ; Google Business Profile Help, https://support.google.com/business/answer/15013580 |
| What share of requests should become a confirmed visit? | Practice-management guidance treats 70 to 80 percent of inbound requests turning into scheduled appointments as healthy for dental and outpatient practices; below that, the front desk is losing demand it already paid to acquire. | Dental Economics, front-desk conversion articles, https://www.dentaleconomics.com ; MGMA practice operations benchmarks, https://www.mgma.com |
| What is a normal no-show rate? | A systematic review across specialties puts the average outpatient no-show rate at about 23 percent worldwide; US primary care and dental practices report 10 to 20 percent, and well-run practices target under 10 percent. MGMA treats 5 to 7 percent as best in class. | Dantas et al., "No-shows in appointment scheduling: a systematic literature review", Health Policy 2018, https://doi.org/10.1016/j.healthpol.2018.02.010 ; Kheirkhah et al., BMC Health Services Research 2016, https://doi.org/10.1186/s12913-015-1243-z |
| What is a normal cancellation rate? | Late cancellations run 10 to 20 percent in outpatient care. Above 20 percent the schedule cannot be filled and chair time is wasted. | Dantas et al. 2018 (above); Journal of the American Dental Association practice-management notes |
| Do reminders work? | SMS reminders cut no-shows by roughly a third in a meta-analysis of 29 trials; two touches (48 hours and same morning) outperform one. | Hasvold and Wootton, "Use of telephone and SMS reminders to improve attendance at hospital appointments: a systematic review", Journal of Telemedicine and Telecare 2011, https://doi.org/10.1258/jtt.2011.110707 ; Robotham et al., BMJ Open 2016, https://doi.org/10.1136/bmjopen-2016-012116 |
| Does lead time matter? | No-show probability rises with the gap between booking and visit; requests booked more than two to three weeks out are the most likely to be missed. A collapse in lead time (everyone booking for tomorrow) instead signals unmet demand or an emergency-heavy mix that the schedule should absorb. | Kheirkhah et al. 2016 (above); Dantas et al. 2018 |
| Weekend and after-hours demand | Customers increasingly want evening and Saturday slots; a request for a day with no posted hours is demand the profile cannot serve, and "open at time of search" is among the strongest local-pack factors. | Whitespark Local Search Ranking Factors, https://whitespark.ca/local-search-ranking-factors/ ; `02-industry-audit-factors.md` Operations section |
| Channel mix | Requests arriving through only one channel mean the others are not wired up: no booking link on the profile, no web form, or phone requests not logged. | Google Business Profile Help, bookings, https://support.google.com/business/answer/7475773 |
| Google's own bookings count | Google reports `BUSINESS_BOOKINGS` only when a Reserve with Google partner is connected. A profile whose CRM receives requests from Google while Google reports zero bookings is not tracking the channel. | `01-google-official-guidance.md` section 2.9 |

## What we have

`bookings` in the snapshot: one row per request with `external_booking_id`, `service`,
`requested_for_date`, `status` (`new`, `confirmed`, `completed`, `cancelled`,
`no_show`), `booking_source` (`website`, `google_profile`, `phone`, `walk_in`) and
`booking_created_at`. `customer_name` is stripped before the snapshot is written and
must never appear in a finding or a prompt.

`performance` daily rows carry Google's `bookings` and `conversations` counts, nullable.

`hours` regular rows say which days the location is open. `projects` carry the
operator's own service list.

Quick stats on `booking_requests.csv` (1,000 rows, 2026-06-15 to 2026-09-11, twelve
locations, analysis date 2026-09-11):

- Status mix: confirmed 540, completed 173, new 152, cancelled 100, no-show 35.
- Lead time between request and requested date: median 11 days, range 0 to 21, stable
  month to month (10, 11, 11, 12).
- Channel mix is even overall (google_profile 270, walk_in 262, phone 240, website 228);
  one location has no website channel at all.
- 26 percent of requests are for a Saturday or Sunday. Some locations post Saturday
  hours, some do not.
- The 152 `new` requests are 12 to 87 days old (median about 40 days); 133 of them are
  for a date that has already passed. 480 `confirmed` requests are also for past dates.
  Statuses are clearly not maintained after the visit.
- Per location, cancelled as a share of settled outcomes (completed, cancelled,
  no-show) runs 25 to 45 percent; no-show 7 to 30 percent. Settled denominators are 4
  to 51 per location.

## What we do not have

No timestamp for when a request was confirmed, so response time is measured only for
requests still waiting. No reminder log. No customer identity, by design. No slot
capacity, so utilisation cannot be judged. No reason codes on cancellations.

## Checks

| Rule | Fails when | Threshold (EngineConfig) | Why |
| --- | --- | --- | --- |
| `requests_unanswered` | a request is still `new` more than `booking_wait_days` after it was made; one finding per request | `booking_wait_days` = 3 | HBR: leads decay within a day; three days is already a lost customer |
| `requests_expired` | `new` requests whose requested date has passed | `booking_wait_days` for the age floor | The visit day came and went with no decision recorded |
| `confirmation_rate_low` | confirmed + completed + no-show share of decidable requests (older than the wait) in the window below the minimum | `booking_confirmation_min` = 0.7, `booking_min_requests` = 10 | Front-desk conversion benchmark 70 to 80 percent |
| `cancellation_rate_high` | cancelled share of settled outcomes above the maximum | `booking_cancellation_max` = 0.2, `booking_min_settled` = 10 | Late cancellations above 20 percent leave chair time empty |
| `no_show_rate_high` | no-show share of settled outcomes above the maximum | `booking_no_show_max` = 0.1, `booking_min_settled` = 10 | Well-run practices target under 10 percent |
| `service_not_listed` | a requested service matches none of the project's services; one finding per service | none | Customers ask for what the profile does not say it offers, or the list is stale |
| `weekend_demand_without_hours` | requests for a Saturday or Sunday with no regular hours for that day; one finding per day | `booking_weekend_min_requests` = 5 | Demand the posted hours cannot serve |
| `lead_time_shrinking` | median lead time in the recent slice below the ratio of the earlier median | `booking_lead_recent_days` = 28, `booking_lead_collapse_ratio` = 0.5 | A collapse means urgent demand the schedule is not absorbing |
| `channel_concentrated` | one channel carries more than the maximum share of requests | `booking_channel_share_max` = 0.9 | Other channels are probably not wired up |
| `google_bookings_untracked` | Google reports zero bookings across the window while the CRM holds requests | none | The booking link is not a Reserve with Google integration, so Google cannot count it |

Every request-level check uses the `booking_window_days` (90) window by creation date.

## Traps

- Statuses are stale. A `confirmed` request for a date long past is probably a visit
  whose outcome was never recorded. Outcome rates therefore use only settled statuses
  (`completed`, `cancelled`, `no_show`) as the denominator, never every request.
- A future visit is not a failure. `confirmed` requests for future dates are healthy.
  `new` requests are only stale by the age of the request, not the date of the visit.
- CRM requests are separate from Google's `bookings` count. They never reconcile and
  must not be compared as if they measured the same thing.
- Small denominators. A location with four settled visits cannot have a no-show rate.
  Every rate check abstains below its floor.
- The service list lives on the project, not the profile. A location with no project,
  or a project with no services, cannot be checked for mismatches.
- Hours absent entirely means unknown, not closed. Weekend demand is only judged when
  hours exist for at least one day.
- Google reporting `null` bookings is not zero. The tracking check needs at least one
  reported day.
