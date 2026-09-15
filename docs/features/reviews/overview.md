# Reviews

The review inbox: read every review of a profile, filter it, and reply — with the reply going
through the provider and landing in the same audit trail as a profile edit.

Code: `app/api/reviews.py`, `app/models/review.py`,
`app/services/providers/reviews.py`. Screens: `frontend/src/components/reviews/`.

## The model

One row per review in `reviews`, unique on `(location_id, google_review_id)`, indexed on
`(location_id, create_time)` — because the inbox is always "one location, newest first".

**The owner reply lives inline**, not in a child table: Google returns `reviewReply` nested
inside the review and allows at most one per review, so a child table would only ever hold
zero or one row.

```
star_rating        1-5 integer, NOT NULL
comment            Text, nullable
create_time        when the customer wrote it
reply_comment      Text, nullable   ← the reply
reply_update_time  when the reply was last edited
```

`reviewer_display_name` and `reviewer_photo_url` are stored but **stripped from the audit
snapshot** and never returned by `ReviewResponse`.

## Endpoints

All under `/api/v1`.

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/reviews` | `project_id`, `location_id`, `rating` (1-5), `replied` (bool), `q`, `limit` (1-200, default 50), `offset` |
| `GET` | `/reviews/summary?location_id=` | Counts and average — declared **before** `/{review_id}` so "summary" is not parsed as a UUID |
| `GET` | `/reviews/{id}` | One review |
| `PUT` | `/reviews/{id}/reply` | Create **or replace** the reply. There is no POST |
| `DELETE` | `/reviews/{id}/reply` | Remove it |
| `POST` | `/reviews/sync` | Pull from the provider |

`q` searches `comment`, `reviewer_display_name` **and** `reply_comment`, escaped `ILIKE`.
`replied=true` means `reply_comment IS NOT NULL`. Ordering is `create_time DESC, id`, the id
making paging stable. `total` is counted before limit/offset.

The summary is a plain SQL aggregate over all stored reviews of a location — no AI:

```json
{"total": 138, "average": 4.31,
 "distribution": {"1": 4, "2": 3, "3": 9, "4": 31, "5": 91}}
```

All five keys are always present, zero-filled; `average` is `null` when `total` is 0.

**There is deliberately no endpoint to delete a review.** Only the reply is ours.

## Related

- [inbox-and-replies.md](inbox-and-replies.md) — the write path, step by step
- [../audit-engine/categories/reputation.md](../audit-engine/categories/reputation.md) — the checks that read these rows
- [../ai-agent/tools.md](../ai-agent/tools.md) — `list_reviews`, `reply_to_review`
