# Insights

What Google reports about a profile: how often it was shown, what people did next, which
searches surfaced it, and what photos are on it.

Code: `app/api/insights.py`. Screens: `frontend/src/components/insights/`, three tabs under
`/insights`.

| Endpoint | Screen | Doc |
| --- | --- | --- |
| `GET /api/v1/insights/performance` | Performance | [performance.md](performance.md) |
| `GET /api/v1/insights/search-terms` | Search terms | [search-terms.md](search-terms.md) |
| `GET /api/v1/insights/media` | Photos | [media.md](media.md) |
| `POST /api/v1/insights/load-sample-data` | — | reloads the CSV datasets |

## The rule that runs through all three

**Empty means absent, not zero.** Every optional metric is nullable, and the loader stores a
blank CSV cell as `NULL`. "Google reported no calls that day" and "Google reported nothing
that day" are different facts, and defaulting to `0` would quietly turn the second into the
first in every chart, every total and every audit verdict.

Consequences you can see:

- SQL `SUM` skips NULLs, so an absent day contributes nothing rather than a zero.
- A NULL stays `null` in the JSON, and the chart plots a **gap**, never a zero.
- `days_with_data` is what disambiguates a genuine zero from a never-reported metric in the
  totals block.

## Loading the datasets

`POST /api/v1/insights/load-sample-data` opens a `SyncRun(kind=performance)` and calls
`load_sample_datasets`, which upserts eight analytics tables plus the attribute catalog on
their natural keys — running it twice changes nothing. Locations the organization has not
imported are skipped in silence.

A `SampleDataError` marks the run failed and returns **503** with the message naming the
missing path. No frontend calls this route; `app/seed.py` does the same work on first boot.

## Related

- [../audit-engine/categories/performance.md](../audit-engine/categories/performance.md) — the trend checks over these rows
- [../audit-engine/categories/content.md](../audit-engine/categories/content.md) — the photo checks
- [../../architecture/provenance.md](../../architecture/provenance.md)
