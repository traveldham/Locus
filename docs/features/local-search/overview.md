# Local search

Where a profile ranks for the keywords we track, and who ranks above it.

Code: `app/api/market.py`, `app/models/seo.py`. Screens:
`frontend/src/components/market/`, under `/market/rankings` and `/market/competitors`.

## None of this comes from Google, and none of it ever can

The module says it plainly:

> There is no ranking API, Google never discloses a competitor's profile, and the tracked
> keyword list is our own configuration.

So every row in all three tables is written `source = locus`, permanently — not "sample data
until Google approves us", but *this category of data has no Google API behind it and never
will*. The product says so on screen rather than letting a user assume it came from their
Google dashboard and then wonder why the numbers never reconcile.

## Three tables

```
tracked_keywords          a keyword we watch for a location
      │  1:n
keyword_ranks             one weekly rank check for that keyword
      │  1:n
competitor_observations   the rivals seen around us, that keyword, that week
```

`CompetitorObservation` has **no `location_id` column at all** — it hangs off the keyword,
because a competitor is only ever observed *in the context of a query*, and the same business
shows up for several keywords. Reaching a location's rivals means going through its keywords.

There is also **deliberately no unique constraint** on competitor observations: a keyword-week
holds several rivals, which is the entire point of the row.

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/api/v1/market/keywords` | `location_id` or `project_id`; every keyword with its latest rank |
| `GET` | `/api/v1/market/rankings` | `tracked_keyword_id` **required**, optional `from`/`to` |
| `GET` | `/api/v1/market/competitors` | `tracked_keyword_id` **required**, optional `week_start` |

None of the three paginates. Every response carries `source: "locus"`.

## Related

- [keywords-and-ranks.md](keywords-and-ranks.md)
- [competitors.md](competitors.md)
- [../audit-engine/categories/visibility.md](../audit-engine/categories/visibility.md) — the eleven checks over these rows
