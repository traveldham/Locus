# Keywords and ranks

## Tracked keywords

`tracked_keywords`, unique on `(location_id, external_keyword_id)`.

```
external_keyword_id   the rank provider's own id — the join key in every feed they send
keyword               "emergency dentist tampa"
search_intent         SearchIntent | None
device                "mobile" / "desktop" — free text, not an enum
tracking_started_on
```

```python
class SearchIntent(StrEnum):
    general = "general";  emergency = "emergency";  cosmetic = "cosmetic"
    pediatric = "pediatric";  implants = "implants"
    orthodontics = "orthodontics";  insurance = "insurance"
```

`device` is deliberately `String(32)` rather than an enum: the device list is the provider's
to extend, and a new value must not fail the load.

## Weekly ranks

`keyword_ranks`, unique on `(tracked_keyword_id, week_start)` — one check per keyword per
week. **Weeks start Monday.**

| Column | Meaning |
| --- | --- |
| `week_start` | The Monday |
| `rank_absolute` | Position in local results, 1 = top. **NULL when not found** |
| `rank_in_local_pack` | 1-3 when the location made the three-result pack, else NULL |
| `found` | Whether the location appeared at all |
| `result_url` | The URL that ranked |

### NULL is a state, not a number

`rank_absolute = NULL` means **not found** in the checked results. It is not rank 0 and it is
not "worst possible". Anything averaging over these rows must **skip** them, never coerce
them — the engine's `position()` helper returns `None` unless `found` is true and the rank is
at least 1.

And being outside the pack is not the same as not being found: a row can legitimately have
`rank_absolute = 12` with `rank_in_local_pack = NULL`.

## The endpoints

```
GET /api/v1/market/keywords?location_id=   (or ?project_id=)
```

Returns every tracked keyword with a `latest_rank`, resolved in one query with a window
function partitioned by keyword, ordered by `week_start DESC, id`. The join is an **outer**
join, so a keyword with no rank checks still appears with `latest_rank: null`. Ordering is
`keyword, id`.

```
GET /api/v1/market/rankings?tracked_keyword_id=&from=&to=
```

`tracked_keyword_id` is required. **No default window** — omitting `from`/`to` returns the
full stored history, oldest week first. Returns the keyword, the points, plus:

- `weeks_in_local_pack` — rows where `rank_in_local_pack` is not NULL
- `weeks_checked` — rows returned, i.e. within the range filter

Note `keyword.latest_rank` here is the last point **within the requested range**, so a `to`
filter changes it; it is not necessarily the globally latest week.

## How the audit reads them

The visibility worker builds weekly **slots** from the latest check — a missing slot is
*unchecked*, not *unfound*. Then:

| Check | Needs |
| --- | --- |
| `tracking_stale` | Latest check within `rank_freshness_days` (21) — otherwise **every rank check abstains** |
| `pack_share_low` | Share of keywords in the pack in the latest week, against 25% |
| `pack_lost` | In the pack in an earlier week of the 4-week window, not in the latest |
| `near_pack_opportunity` | Positions 4-8 in 2+ of the window's weeks, not in the pack now |
| `not_found_persistent` | `found = false` in **4 consecutive weeks ending in the latest** |
| `rank_dropped` | Latest position worse than the mean of the earlier weeks by 3+ |
| `high_intent_lagging` | A keyword whose intent is emergency / implants / orthodontics sitting 3 behind the median of the others |
| `branded_not_first` | A keyword carrying a brand word not at position 1 |

Brand words are the words of the stored name minus the trade words and the city — so
"riverside grill" is branded for *Riverside Grill*, and "restaurant austin" is not.

See [../audit-engine/categories/visibility.md](../audit-engine/categories/visibility.md).

## Known gaps

- `marketApi.listKeywords` never sends `project_id`, so that filter has no frontend caller.
- The TypeScript comment claims the API picks its own window when `from`/`to` are omitted. It
  does not — it returns everything. Both call sites omit the range, so no date filter is ever
  sent today.
