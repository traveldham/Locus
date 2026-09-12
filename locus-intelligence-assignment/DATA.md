# Data dictionary

All files are UTF-8 CSV with a header row, in `data/`. Dates are `YYYY-MM-DD`. Booleans are
`TRUE`/`FALSE`. An empty field means the value is genuinely absent, not zero.

`location_id` (`LOC-001` … `LOC-012`) is the join key across every file. "Today" for this snapshot
is **2026-09-11**.

The export is synthetic and simplified: fewer columns than production, one organisation, one
business category. It is not cleaned for you, and it is not guaranteed to be complete.

---

## `locations.csv` — 12 rows
One row per clinic. The spine of the dataset.

| column | notes |
|---|---|
| `location_id` | internal id, join key |
| `gbp_location_id` | Google Business Profile resource name |
| `store_code` | the operator's own store code |
| `name`, `primary_category`, `additional_categories` | `additional_categories` is `\|`-separated |
| `city`, `state`, `postal_code`, `latitude`, `longitude` | |
| `phone`, `website_url` | |
| `description` | the business description text shown on the profile; empty when none is set |
| `description_length` | character count of `description` |
| `opened_on` | |
| `verified` | whether the profile is verified with Google |
| `open_status` | `OPEN`, `CLOSED_TEMPORARILY`, `CLOSED_PERMANENTLY` |

## `location_hours.csv` — 84 rows
Regular opening hours, one row per location per weekday. `open_time`/`close_time` are 24h `HH:MM`;
both empty means closed that day.

## `location_daily_kpis.csv` — 1,068 rows
Daily Google Business Profile performance, 2026-06-15 → 2026-09-11, one row per location per day.

| column | notes |
|---|---|
| `impressions_maps_desktop`, `impressions_maps_mobile`, `impressions_search_desktop`, `impressions_search_mobile` | times the profile was shown, split by surface × device |
| `website_clicks` | clicks through to the website |
| `call_clicks` | taps on the call button |
| `direction_requests` | direction requests from the profile |
| `conversations` | messages started from the profile |
| `bookings` | bookings attributed to the profile |

An impression is a view of the profile; the other columns are actions taken from it.

## `location_search_terms_monthly.csv` — 959 rows
The queries that surfaced each profile, aggregated per month, 2026-04 → 2026-08.
Columns: `location_id`, `year_month` (`2026-04`), `search_term`, `impressions`.
Google truncates the long tail, so these do not sum exactly to the daily impression totals.

## `attribute_catalog.csv` — 34 rows
The attributes Google offers for this business category. This is the full menu, not what any
location has set.
Columns: `attribute_id`, `attribute_name`, `attribute_group`
(`accessibility` | `payments` | `services` | `amenities` | `planning` | `identity`),
`applies_to_category`, `value_type`.

## `location_attributes.csv` — 255 rows
Long format: one row per attribute a location has actually set.
Columns: `location_id`, `attribute_id`, `value`.
An attribute set to `FALSE` and an attribute never filled in are different states: the first is a
row with `FALSE`, the second is no row at all.

## `location_media_summary.csv` — 12 rows
Photo and video counts on the profile.
Columns: `location_id`, `photo_count`, `interior_photo_count`, `exterior_photo_count`,
`team_photo_count`, `video_count`, `has_profile_photo`, `has_cover_photo`,
`last_photo_uploaded_on`. The category counts do not have to sum to `photo_count`; the remainder
is uncategorised.

## `reviews.csv` — 1,514 rows
Public Google reviews, 2025-09-01 → 2026-09-10.
Columns: `review_id`, `location_id`, `reviewer_name`, `rating` (1–5 integer), `review_text`,
`created_at`.

## `review_replies.csv` — 874 rows
The owner's public reply, where one exists. Not every review has one.
Columns: `review_id`, `reply_text`, `replied_at`.

## `posts.csv` — 93 rows
Google Business Profile posts published by each location, 2026-03-01 → 2026-09-10.
Columns: `post_id`, `location_id`, `post_type` (`STANDARD` | `EVENT` | `OFFER`), `summary`,
`cta_type` (`BOOK` | `CALL` | `LEARN_MORE` | `SIGN_UP` | `GET_OFFER`, may be empty), `published_on`.

## `booking_requests.csv` — 1,000 rows
Appointment requests received, 2026-06-15 → 2026-09-11.
Columns: `booking_id`, `location_id`, `customer_name`, `service`, `requested_for_date`,
`status` (`new` | `confirmed` | `completed` | `cancelled` | `no_show`),
`source` (`website` | `google_profile` | `phone` | `walk_in`), `created_at`.

## `tracked_keywords.csv` — 112 rows
The local-search keywords being tracked for each location.
Columns: `keyword_id`, `location_id`, `keyword`, `search_intent`
(`general` | `emergency` | `cosmetic` | `pediatric` | `implants` | `orthodontics` | `insurance`),
`device`, `tracking_started_on`.

## `keyword_rank_weekly.csv` — 1,411 rows
One rank check per tracked keyword per week, week starting Monday, 2026-06-15 → 2026-09-07.

| column | notes |
|---|---|
| `keyword_id`, `location_id`, `week_start` | |
| `rank_absolute` | position in local results, 1 = top; empty when not found |
| `rank_in_local_pack` | 1–3 when the location made the 3-result local pack, else empty |
| `found` | whether the location appeared at all in the checked results |
| `result_url` | the URL that ranked |

## `competitor_ranks_weekly.csv` — 4,233 rows
For every keyword-week, the three competing businesses ranked around the tracked location.

| column | notes |
|---|---|
| `keyword_id`, `week_start` | joins to `keyword_rank_weekly.csv` |
| `competitor_name`, `competitor_place_id` | `competitor_place_id` is stable per business |
| `rank_absolute` | the competitor's position that week |
| `review_count`, `average_rating`, `photo_count`, `is_claimed` | the competitor's profile as observed that week |

---

## Known limits of this export

- Daily KPIs cover a quarter; reviews cover a year; search terms cover five months. The windows do
  not line up, and joining across them needs care.
- Google's own reporting rounds and truncates, so totals across files will not reconcile exactly.
- Nothing here is labelled or scored. There are no outcome columns.
