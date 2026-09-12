# 017 — End-to-end data verification

**Date:** 2026-09-13
**Method:** logged in as the demo user against the running backend, called every endpoint, and compared the responses field-by-field against the source CSVs in `locus-intelligence-assignment/data/`.

---

## Bottom line

**The data is correct.** Every row of every seeded dataset reconciles exactly against its CSV. No wrong numbers were found anywhere.

| Dataset | CSV | API | Result |
|---|---|---|---|
| Locations | 12 | 12 | ✅ |
| Hours periods | 84 rows → 71 periods (13 closed days skipped) | 71 | ✅ |
| Attributes | 255 | 255 | ✅ |
| Reviews | 1,514 (874 replied) | 1,514 / 874 | ✅ |
| Performance days | 1,068 | 1,068 | ✅ |
| Search terms | 959 | 959 | ✅ |
| Media rollups | 12 | 12 | ✅ |
| Posts | 69 | 69 in DB | ⚠️ no endpoint |
| Bookings | 1,000 | 1,000 | ✅ |
| Tracked keywords | 112 | 112 | ✅ |
| Keyword ranks | 1,411 | 1,411 | ✅ |
| Competitor observations | 4,233 | 4,233 | ✅ |

Also verified: every filter returns the CSV's own count, pagination reports an honest `total` across full walks, org scoping produced a scoped 404 on all 13 bogus-UUID probes, and there were no unexpected 4xx or 5xx responses.

---

## Open items — not yet fixed

### 1. Posts are loaded but unreachable

69 posts sit in the database, byte-for-byte correct (all 69 verified by `google_post_id`; the 12 empty `cta_type` values are `NULL`, not coerced). There is **no API route**, so nothing can read them.

Loader: `app/services/sample_datasets.py`. Needs an endpoint plus a UI surface, or the data is dead weight.

### 2. `GET /locations` returns a bare array

Every other list endpoint returns `{items, total, limit, offset}`. This one returns a plain list, so a caller cannot tell how many rows exist in total. Pagination itself works correctly (limit 5 across three pages returned 5+5+2 = 12 distinct, no overlap) and `limit=201` is rejected — it simply cannot report `total`.

File: `app/api/locations.py`.

### 3. Two different concepts are both called `source`

This is the one most likely to cause a real mistake later.

| Field | Values | Means |
|---|---|---|
| `Location.source` | `google` / `fixture` / `manual` | where this row was loaded from |
| `DataSource` | `google` / `locus` | who supplies this *kind* of data |

Locations currently return `"source": "fixture"` — which is not a provenance value at all — and reviews carry no `source` field. Hours and attributes, nested inside `LocationDetail`, have none either.

The `locus`-marked tables are all correct: bookings, tracked keywords, keyword ranks and competitor observations. So are performance, search terms, media and posts on the `google` side. The gap is only on locations, hours, attributes and reviews.

Renaming one of the two would remove a standing trap.

### 4. Minor

- `limit` above 200 returns **422** rather than clamping to the cap. Intentional rejection is defensible; just note it is not a clamp.
- `year_month=2026-13` is accepted (`200`, empty result). The pattern is `^\d{4}-\d{2}$` with no month-range check.
- Org scoping resolves to the caller's **first** membership (`app/api/scoping.py`). Correct today with one org, but a user in two organizations would have no way to reach the second.

---

## Not a bug: LOC-010's website

The CSV says `https://brightpathdental.com/phoenix-arcadia`; the API returns `brightpathdental.om` — missing the `c`.

That is a **real user edit**, not a seeding fault. `GET /locations/{id}/actions` shows one `location_update`, status `succeeded`, at `2026-09-12T19:34:07Z`, `update_mask: ["websiteUri"]`, with `current` and `proposed` matching the two strings exactly.

So the edit → preview → confirm → audit chain is proven end to end on real data. The typo is worth correcting in the app.

---

## Traps that could not be sprung

Three checks were aimed at failure modes the sample data does not actually contain. The code handles all three correctly; the data simply never exercises them.

| Trap | Why it could not fire |
|---|---|
| **Nulls becoming zeros** | `location_daily_kpis.csv` has **zero** empty cells across 9 metrics × 1,068 rows. Schemas are null-safe regardless, and nulls that *do* exist elsewhere are handled right: 80 `rank_absolute`, 1,316 `rank_in_local_pack`, 12 post `cta_type`, LOC-003's empty website all return `null`. |
| **`is_threshold`** | The CSV has **no such column**. The loader reads it and correctly defaults to `false`, so no value is presented as exact when it is not. The flag is modelled end to end with nothing to carry. |
| **Multi-period / overnight hours** | The CSV contains **no** multi-period days and **no** overnight rows. Proven working instead via a non-mutating `edits/preview` dry run: two Monday periods plus an overnight Friday 22:00 → Saturday 02:00 came back intact with `update_mask: ["regularHours"]`, `valid: true`. |

Worth remembering: **passing a test the data cannot fail proves nothing.** If these paths matter in production, the sample data needs rows that exercise them.

---

## Confirmed correct in detail

- **Totals skip nulls.** All 11 total fields recomputed from CSV for all 12 locations over the full range: 0 discrepancies. Org-wide `website_clicks` 20,073 = 20,073.
- **`rank_absolute` vs `found`.** 80 empty ranks and 80 `found=FALSE` rows are the *same* 80 rows. Never plotted as 0.
- **Reviews.** All 1,514 match on location, reviewer, date, rating and text; all reply texts and timestamps match; rating distribution identical (1→90, 2→90, 3→111, 4→311, 5→912).
- **Attribute types.** Booleans come back as real JSON booleans. The one `enum` attribute stays string-valued, faithful to `attribute_catalog.csv`.
- **Competitors.** Exactly 3 per keyword-week across 1,411 weeks = 4,233; never returned under the wrong week.
- **Bookings `created_at`** is the CSV's booking timestamp, not the database row-write time — the two are different columns and the right one is exposed.
- **`bookings.status_counts`** respects `location_id` and `booking_source` but deliberately ignores `status`. That is correct facet behaviour, not a bug.

## Not checked

Mutating endpoints were left alone to avoid changing state: project create/update/delete, add/remove project locations, review reply/delete-reply/sync, `POST /locations/{id}/edits`, and `POST /insights/load-sample-data`. The edit path was verified indirectly through the LOC-010 audit row.
