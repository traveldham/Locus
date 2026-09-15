# The dataset

Fourteen CSVs in `locus-intelligence-assignment/data/`, UTF-8 with a header row. Dates are
`YYYY-MM-DD`, booleans are `TRUE`/`FALSE`, and **an empty field means the value is genuinely
absent, not zero**.

`location_id` (`LOC-001` … `LOC-012`) is the join key across every file. **"Today" for this
snapshot is 2026-09-11.**

The export is synthetic and simplified — fewer columns than production, one organisation, one
business category. It is not cleaned, and it is not guaranteed to be complete.

## The files

| File | Rows | Holds | Loaded into |
| --- | --- | --- | --- |
| `locations.csv` | 12 | The spine: name, categories, address, phone, website, description, `verified`, `open_status` | `locations` (via the provider) |
| `location_hours.csv` | 84 | Regular hours, one row per location per weekday | `location_hours_periods` |
| `location_attributes.csv` | 255 | Long format: one row per attribute a location has **set** | `location_attribute_values` |
| `attribute_catalog.csv` | 34 | The full menu Google offers for this category | `attribute_catalog_items` |
| `reviews.csv` | 1,514 | Public reviews, 2025-09-01 → 2026-09-10 | `reviews` |
| `review_replies.csv` | 874 | The owner's reply where one exists | `reviews.reply_comment` |
| `location_daily_kpis.csv` | 1,068 | Daily performance, 2026-06-15 → 2026-09-11 | `performance_daily` |
| `location_search_terms_monthly.csv` | 959 | Queries that surfaced each profile, 2026-04 → 2026-08 | `search_terms_monthly` |
| `location_media_summary.csv` | 12 | Photo and video counts | `media_summary` |
| `posts.csv` | 93 *(see below)* | Posts, 2026-03-01 → 2026-09-10 | `posts` |
| `booking_requests.csv` | 1,000 | Appointment requests, 2026-06-15 → 2026-09-11 | `bookings` |
| `tracked_keywords.csv` | 112 | The local-search keywords tracked per location | `tracked_keywords` |
| `keyword_rank_weekly.csv` | 1,411 | One rank check per keyword per week, Mondays | `keyword_ranks` |
| `competitor_ranks_weekly.csv` | 4,233 | Three rivals per keyword-week | `competitor_observations` |

About 8,900 rows land in the analytics tables; the profile, hours, attribute and review files
go in through the provider path.

## The traps, and what the engine does about each

These are the things that will produce a wrong answer if you do not notice them. Every one is
handled explicitly in code.

**1. An empty cell is absent, not zero.** Google omits a metric for a day it has no data for.
Defaulting to `0` turns "Google did not report calls" into "nobody called" in every chart and
every verdict. → every metric column is nullable, and the audit abstains.

**2. A `FALSE` attribute and a missing attribute are different states.** The first is an
answer; the second is unknown. → `attributes_sparse` counts an explicit no as *answered*;
`accessibility_unanswered` fires only on the missing row. Never infer a service exists.

**3. `rank_absolute` empty means not found, not rank 0.** → `position()` returns `None`
unless `found` is true, and nothing averages over it. "Not found" is a state.

**4. Being outside the local pack is not the same as not being found.** A row can have
`rank_absolute = 12` and `rank_in_local_pack` empty. → two separate checks.

**5. The windows do not line up.** Daily KPIs cover a quarter, reviews a year, search terms
five months. Joining across them needs care. → each worker declares its own window, and
nothing is joined into a funnel that the data cannot support.

**6. Google truncates and rounds.** Search-term totals will not reconcile with daily
impressions, and never should. → the search-term checks compare only two exact complete
months, and only above an impressions floor.

**7. Statuses are current state, often stale.** A booking marked `new` may have been answered
by phone. → a `new` request is judged stale by the age of the *request*, never the date of the
visit; `confirmed` for a past date is excluded from every outcome rate rather than counted as
a failure.

**8. Competitor figures are scraped observations.** They are not measured the way our own
stored counts are. → rivals are compared only inside the same keyword and week, and the
comparison is marked medium confidence with the mismatch stated in the finding.

**9. Nothing is labelled.** There is no outcome column, so there is nothing to learn from and
nothing to validate a prediction against. → the engine predicts nothing. It reports what is
observed and ranks the work.

## A discrepancy worth recording

`DATA.md` states `posts.csv` has **93 rows**. The shipped file contains **69**. The original
write-up flagged it, and the engine handles it by treating zero or few posts as an
*observation* reported with **medium confidence**, carrying the limitation that an incomplete
export looks exactly the same as never posting.

That is the pattern for every ambiguity in this dataset: say what was observed, say what it
cannot distinguish, and do not let the score assert more than the data supports.

## Where the data goes

```
locations.csv ─┬─ location_hours.csv ─┬─→ SampleGbpProvider ──→ upsert_location ──→ locations
               └─ location_attributes.csv           (+ hours, categories, attributes)
                  attribute_catalog.csv

reviews.csv ──── review_replies.csv ──→ SampleReviewsProvider ──→ reviews

the other eight ────────────────────→ load_sample_datasets ──→ the analytics tables
```

Two loaders, because the first group is the *profile* — the shape a Google API would return —
and the second is analytics that has nowhere to sit on a profile object.

`SAMPLE_DATA_DIR` overrides the directory; the default is `<repo>/locus-intelligence-assignment/data`.
