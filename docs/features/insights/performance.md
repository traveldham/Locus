# Performance

Daily Google Business Profile metrics: impressions split by surface and device, and the
actions customers took from the profile.

## The table

`performance_daily`, unique on `(location_id, date)`, indexed on `(organization_id, date)`
for org-wide rollups. **Every metric is nullable on purpose.**

| Column | Meaning |
| --- | --- |
| `impressions_maps_desktop` | Times the profile was shown, by surface × device |
| `impressions_maps_mobile` | |
| `impressions_search_desktop` | |
| `impressions_search_mobile` | |
| `website_clicks` | Clicks through to the website |
| `call_clicks` | Taps on the call button |
| `direction_requests` | Direction requests |
| `conversations` | Messages started from the profile |
| `bookings` | Bookings Google attributes to the profile |

An impression is a view of the profile; the rest are actions taken from it. **Actions are
events, not customers** — one person can call twice.

## The endpoint

```
GET /api/v1/insights/performance
    ?location_id=  &project_id=  &from=YYYY-MM-DD  &to=YYYY-MM-DD
```

- `from` and `to` are aliases; internally `start` and `end`.
- **There is no server-side default window and no maximum range.** Omitting both returns every
  stored day for the scope. The window is the client's choice — the UI opens on the last 30
  days.
- With no `location_id`, metrics are **summed across locations in SQL**, giving a portfolio
  view. `location_id` is echoed back as `null` in that case.
- Ordering is ascending by date.

Response:

```json
{"location_id": "…", "start_date": "…", "end_date": "…",
 "points": [{"date": "2026-09-01", "impressions_maps_desktop": 12, …}],
 "totals": {"impressions_total": …, "impressions_maps": …, "impressions_search": …,
            "impressions_desktop": …, "impressions_mobile": …,
            "website_clicks": …, "call_clicks": …, "direction_requests": …,
            "conversations": …, "bookings": …, "days_with_data": 28},
 "source": "google"}
```

Every field on a point is `int | null`. Totals are derived: `impressions_total` is all four
impression sums; `impressions_maps` is the two maps columns; `impressions_mobile` is the two
mobile columns; and so on.

`days_with_data` counts distinct dates where **any** of the nine metrics is non-NULL.

## How the audit reads the same rows

The performance worker does something quite different from the chart, and the difference
matters:

- Windows are `performance_window_days` (28, a multiple of 7) and **end on the last day with
  data on or before the audit date**, never on the audit date itself.
- Each current day is **paired with the same weekday one window earlier**; only days both
  windows report are compared. A missing day is unknown, so it and its pair are dropped. A
  NULL metric is unknown, so each metric pairs on its own.
- At least `performance_min_paired_share` (70%) of days must pair, and both windows need
  `performance_min_impressions` (200), or the check abstains.
- Data newer than `performance_max_stale_days` (14) before the audit date is required;
  otherwise every check abstains with the age in the reason.
- A zero-action streak requires impressions on each day, so "no data" never reads as "nobody
  acted".

See [../audit-engine/categories/performance.md](../audit-engine/categories/performance.md).

## Known gap

The frontend totals tiles read `totals.impressions` and then fall back to summing the
per-surface keys (`impressions_maps_desktop`, …) out of `totals`. **Neither exists** in the
response — the backend emits `impressions_total`, `impressions_maps`, `impressions_search`,
`impressions_desktop`, `impressions_mobile`. So those tiles resolve to "not reported" even
when the backend computed the number. The five action tiles do match.
