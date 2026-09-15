# Competitors

For every keyword-week, the businesses ranked around the tracked location.

## The table

`competitor_observations` — indexed on `(tracked_keyword_id, week_start)`, which is exactly
the access path the endpoint uses.

```
tracked_keyword_id     the keyword this was observed under  ← no location_id
week_start             the Monday
competitor_name
competitor_place_id    stable per business, separately indexed
rank_absolute          their position that week
review_count           \
average_rating          |  their profile as observed that week —
photo_count             |  a snapshot, not a live figure
is_claimed             /
```

`competitor_place_id` is the stable key for following one rival across keywords and weeks.

**No unique constraint, on purpose.** A keyword-week holds several rivals. The sample loader
therefore deletes per keyword-week before re-inserting rather than upserting.

## The endpoint

```
GET /api/v1/market/competitors?tracked_keyword_id=&week_start=
```

`tracked_keyword_id` is required. If `week_start` is omitted the server resolves it to
`MAX(week_start)` for that keyword — the most recent observed week, which is what the screen
opens on — and **echoes back the week it chose**. If the keyword exists but nothing was ever
observed, it returns empty with `week_start: null`.

Ordering is `rank_absolute ASC NULLS LAST, competitor_name` — unranked rivals after ranked
ones, alphabetical tiebreak.

## How the audit reads them

Two checks, and both are careful about what a competitor row can support.

**`rival_ahead_gap`** (visibility). Rivals are compared **only inside the same keyword and the
same week**, and only when our profile was checked on that keyword that week. A rival counts
as ahead when its `rank_absolute` is better than ours — or when we were not found at all. A
rival ahead on `rival_min_keywords_ahead` (3) or more keywords is then checked for a profile
gap against our own figures:

| Gap | Threshold |
| --- | --- |
| reviews | `rival_review_ratio` — 1.5× our stored review count |
| rating | `rival_rating_gap` — +0.3 over our mean star rating |
| photos | `rival_photo_ratio` — 1.5× our `photo_count` |

Our side comes from the `reviews` and `media` rows in the snapshot, so the comparison is
between two things measured differently — which the finding's limitation says out loud.

**`reviews_few_vs_competitors`** (reputation). Takes each keyword's **latest observed week**,
medians the competitor review counts within it, then medians across keywords — so one crowded
keyword cannot dominate. Our stored review count below `competitor_review_ratio_min` (50%) of
that median fires the check, at **medium confidence**: stored reviews and a scraped competitor
figure are not measured the same way.

This is also the one reputation check that still fires with **zero** stored reviews, because
zero against a known competitor median is exactly what it measures.

## What is deliberately not claimed

- No causal ranking explanation. A rival being ahead with more reviews is a description, not
  a mechanism.
- No cross-week or cross-keyword comparison.
- Competitor categories and services are not in the export, so relevance gaps cannot be
  distinguished from prominence gaps.

## Known gap

The TypeScript `Competitor` interface omits `id`, `tracked_keyword_id`, `week_start` and
`source`, and types `competitor_place_id` and `is_claimed` as non-nullable when the API
returns them nullable.
