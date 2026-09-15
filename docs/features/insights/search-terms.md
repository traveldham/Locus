# Search terms

The queries that surfaced a profile, aggregated per month.

## The table

`search_terms_monthly`, unique on `(location_id, year_month, search_term)`.

`year_month` is `String(7)` — `"2026-04"` — stored as text deliberately: the month is the
whole grain here, and a date column would invite a misleading day component.

## `is_threshold` — the field that matters

Google returns a term's volume as **either** an exact `value` **or** a `threshold` ("fewer
than 15"), never both. It withholds the exact number for low-volume terms.

```
is_threshold = false  →  impressions is a measured count
is_threshold = true   →  impressions is a ceiling. Render it as "<15".
```

A term reported as "under 15" must never be charted, summed or ranked as if it were exactly
15. The audit enforces this by refusing to pair a threshold row at all — only two exact
months are ever compared.

Because Google truncates the long tail, these totals **do not reconcile** with the daily
impression figures, and nothing in the product tries to make them.

## The endpoint

```
GET /api/v1/insights/search-terms
    ?location_id=  &year_month=YYYY-MM  &limit=  &offset=
```

`year_month` is pattern-validated `^\d{4}-\d{2}$`; omitted means all months. `limit` 1-200,
default 50. Ordering is `impressions DESC NULLS LAST, id` — highest first, unmeasured terms
last, id for stable paging. `total` is counted before paging.

## How the audit reads them

Two checks in the visibility worker:

- **`search_term_losing`** pairs the **latest complete month** with the one before it. Both
  must carry an exact count, and the earlier month must be at or above
  `term_loss_min_impressions` (200), before a loss of `term_loss_share` (50%) or more is
  reported. The month of the analysis date is incomplete and is never compared.
- **`service_not_surfacing`** looks for a project service whose words (longer than three
  letters) appear in none of the latest month's terms.

See [../audit-engine/categories/visibility.md](../audit-engine/categories/visibility.md).
