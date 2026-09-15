# Photos and video

## It is a rollup, not the photos

`media_summary` holds **counts**, one row per location (`UniqueConstraint("location_id")` — a
second row would mean two answers to the same question).

The live Google API returns individual media items (`locations.media.list`), each with its own
id, category, URL and upload time; these counts would be *derived* from that list, not fetched
as counts. Keeping that explicit bounds what the table can answer: it can say "44 photos, 15
of them interior", but it can never **show** a photo, attribute one to an uploader, or delete
one. When media items land they get their own table and this becomes a cache of them.

```
photo_count               interior_photo_count   exterior_photo_count
team_photo_count          video_count
has_profile_photo (bool)  has_cover_photo (bool)
last_photo_uploaded_on
```

**The category counts need not sum to `photo_count`.** The remainder is uncategorised, and
the UI reports it as "other". A null count is unknown for that check only — not zero.

## The endpoint

```
GET /api/v1/insights/media?location_id=
```

No pagination, no limit, no date filter — there is at most one row per location. Ordering is
`Location.title, id`. `total` is the number returned, not a database count. The response has
no `id` field.

## How the audit reads them

The content worker owns five photo checks — `photos_few` (below 10), `photos_below_target`
(below 30), `photo_type_empty` (one finding per empty type), `video_missing`, `photos_stale`
(last upload over 90 days ago) — and the **profile** worker owns two more, `logo_missing` and
`cover_photo_missing`, reading `has_profile_photo` / `has_cover_photo`.

An absent media row abstains every photo check. A null count abstains only its own.

The visibility worker also reads `photo_count` as *our* side of the rival comparison: a
competitor with `rival_photo_ratio` (1.5×) our photos counts as a gap.

`photos_few`, `photos_below_target` and `photo_type_empty` declare
`suggests: "photo_shot_list"`, so the suggestion layer drafts five to eight specific shots,
each under 120 characters, matched to the empty type and the business category.

See [../audit-engine/categories/content.md](../audit-engine/categories/content.md).
