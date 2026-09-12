# 018 — CSV → database → API → UI reconciliation

**Date:** 2026-09-13  
**Status:** DONE

Every source CSV was traced through parsing, persistence, API serialization and its visible
surface. Counts were checked against the running PostgreSQL database after migration and a full
idempotent reseed.

| CSV | CSV rows | Database rows | UI surface | Coverage |
|---|---:|---:|---|---|
| `locations.csv` | 12 | 12 | Locations and location detail | Complete |
| `location_hours.csv` | 84 | 71 periods | Location detail → Hours | Complete; 13 closed days correctly become no period |
| `attribute_catalog.csv` | 34 | 34 | Location detail → Attributes | Complete; configured and unset states shown |
| `location_attributes.csv` | 255 | 255 | Location detail → Attributes | Complete; false remains distinct from unset |
| `location_daily_kpis.csv` | 1,068 | 1,068 | Insights → Performance | Complete; all nine metrics |
| `location_search_terms_monthly.csv` | 959 | 959 | Insights → Search terms | Complete |
| `location_media_summary.csv` | 12 | 12 | Insights → Photos | Complete |
| `reviews.csv` | 1,514 | 1,514 | Reviews | Complete |
| `review_replies.csv` | 874 | 874 joined replies | Reviews | Complete |
| `posts.csv` | 69 | 69 | Posts | Complete after this task |
| `booking_requests.csv` | 1,000 | 1,000 | Bookings | Complete, including external booking ID |
| `tracked_keywords.csv` | 112 | 112 | Market → Rankings / Competitors | Complete |
| `keyword_rank_weekly.csv` | 1,411 | 1,411 | Market → Rankings | Complete, including result URL |
| `competitor_ranks_weekly.csv` | 4,233 | 4,233 | Market → Competitors | Complete, including Place ID |

## Field decisions

- `locations.description_length` is derived from `description`; it is not duplicated in the
  database. The complete description is shown, so no source content is lost.
- `locations.location_id` is preserved as `source_location_id` as well as being used to join every
  feed. The UI displays it beside the Google identifiers.
- Closed weekday rows contain no hours and intentionally produce no database period. The Hours UI
  reconstructs those days as `Closed`.
- Attribute catalog rows are now permanent data rather than a parser-only lookup. The UI shows
  official name, group, category, type and whether each item is configured.
- Empty CSV cells remain `NULL`, never zero. UI surfaces render them as absent/not reported.
- Internal organization and foreign-key UUIDs remain implementation details; user-relevant
  external identifiers are visible as secondary metadata.

## Verification

```bash
cd backend
uv run alembic upgrade head
uv run python -m app.seed
uv run ruff check .
uv run ruff format --check .
uv run pytest -q

cd ../frontend
npm run lint
npx tsc --noEmit
npm run build
```

Live checks against the running applications returned 69 posts, 34 catalog items across six
groups, and HTTP 200 for `/posts`.

The strict field pass also confirmed that organization-wide search-term rows identify their
location; reviews show their Google review ID; tracked keywords show their external keyword ID;
rank checks link to `result_url`; and competitor rows show their Place ID.
