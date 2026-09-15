# Posts

Google Business Profile posts published by a location. **Read-only in this build.**

Code: `app/api/posts.py`, `app/models/content.py`. Screen:
`frontend/src/components/posts/posts-view.tsx`.

## The one endpoint

```
GET /api/v1/posts
    ?location_id=  &project_id=  &post_type=  &limit=  &offset=
```

`limit` 1-200, default 25. Ordering is `published_on DESC NULLS LAST, id`. `total` is counted
before paging. There is **no detail, create, update or delete route** — Google post
publishing is not built.

## The model

`posts`, unique on `(location_id, google_post_id)` so a re-sync updates in place.

```python
class PostType(StrEnum):
    standard = "standard"
    event    = "event"
    offer    = "offer"
    alert    = "alert"

class PostCtaType(StrEnum):
    book = "book"; call = "call"; learn_more = "learn_more"
    sign_up = "sign_up"; get_offer = "get_offer"
```

`cta_type` is **nullable**, and deliberately has no `"none"` member: Google allows a post
with no call to action, and a `none` member would be indistinguishable from an unset value.

`published_on` is nullable. A post with no readable date is ignored by the audit rather than
guessed at.

## Where the rows come from

Only the sample dataset loader, reading `posts.csv`. A row is skipped when the location is
unknown, `post_id` is blank, or `post_type` is not a `PostType` member; an unrecognised
`cta_type` becomes `None`. Rows are written with `source = google` because posts *are* a
Google dataset, even though these particular ones came from a CSV.

There is no posts sync endpoint and no posts provider.

## What the audit does with them

Four checks in the content worker, and they are where posts earn their keep:

| Check | Fires when |
| --- | --- |
| `posts_none_recent` | Last post older than 30 days, or **no post at all** (critical) |
| `posts_sparse` | Fewer than 6 posts in 90 days |
| `post_types_uniform` | Every post in the 180-day window is one type |
| `posts_without_cta` | Over half the window's posts carry no button |

The 180-day window mirrors Google's six-month post archive: the audit judges what a customer
can still see. Post type and CTA values are casefolded, so the export's `STANDARD` and the
model's `standard` are one thing.

All four declare `suggests: "post_drafts"`, so the suggestion layer drafts **exactly two**
posts — one update, one offer or event — each under 300 characters and ending with the button
it should carry.

See [../audit-engine/categories/content.md](../audit-engine/categories/content.md).
