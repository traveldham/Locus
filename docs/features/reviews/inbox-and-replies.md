# Replying to a review

A reply is a **real write**, not a database update. It goes through the provider and is
recorded in `profile_actions` exactly like a profile edit.

## The write path

`PUT /api/v1/reviews/{id}/reply` with `{"comment": "..."}` — 1 to 4096 characters.

```
1. ProfileAction(action_type="reply_to_review", status=pending)   [committed]
2. status → executing                                             [committed]
3. provider.reply(connection, location, google_review_id, comment)
4a. ProviderError    → status=failed, error set        → 502
4b. success          → mirror locally, status=succeeded
```

The action's `payload` carries `review_id`, `google_review_id` and the `comment`. On success
`google_response` records `{"google_review_id": ..., "reply_update_time": ...}`.

Mirroring uses the provider's own values when it returns them, falling back to what was sent:

```python
review.reply_comment    = result.reply_comment or comment
review.reply_update_time = result.reply_update_time or utcnow()
```

`DELETE` is the same shape with `action_type="delete_review_reply"`, and sets both columns
back to `None`. A review with no reply is a **404 "This review has no reply to remove"**.

## Errors

| Code | When |
| --- | --- |
| `404` | Unknown review, unknown location, or another tenant's |
| `409` | "Connect a Google account first" — the organization has no `GoogleConnection` |
| `422` | Whitespace-only comment, or over 4096 characters |
| `502` | `ProviderError`, with the provider's message |

The router re-checks the comment after Pydantic: a stripped-empty body is
*"A reply cannot be empty"*.

**Note:** these action rows share `location_id` with profile edits, so they appear in
`GET /locations/{id}/actions` — the profile's "Change history" — because they *are* writes
against that location.

## Sync

`POST /api/v1/reviews/sync` takes an optional `location_id`. It opens a `SyncRun(kind=reviews,
status=running)`, then per location:

- A location with a blank `google_resource_name` is **skipped** with a reason, and is not
  counted in `locations_synced` — reviews are a v4 API and need the account-qualified name.
- Otherwise `provider.list_reviews(...)`, upserted on `google_review_id` within the location,
  so re-syncing updates in place.

A `ProviderError` marks the run `failed` with the error text and returns 502. Success records
`records_written = created + updated`.

```json
{"sync_run_id": "…", "locations_synced": 12, "created": 4, "updated": 1510,
 "total": 1514, "skipped": []}
```

**Known gap:** `location_id` is declared as a bare scalar on the handler, so FastAPI binds it
as a **query** parameter. The frontend sends it in a JSON body, which is therefore ignored —
the sync always runs across every location of the organization.

## AI involvement

None in this router. Two adjacent systems produce reply text, and both publish through this
same endpoint — there is no AI-specific reply route:

- **The audit's suggestion layer** drafts a `review_reply` for each unanswered 1-3 star
  review: under 350 characters, no names, phone numbers, email addresses, links, promotions
  or discounts, enforced in code after the model answers.
- **The agent** can call `reply_to_review` directly, and `list_audit_suggestions` lets it
  publish the audit's own draft rather than inventing its own wording.

The frontend publishes drafts from the suggestion panel, the reputation card and the bulk
reply panel, all through `useReplyToReviewMutation`.

## The star rating

The model's comment says Google sends the rating as an enum string (`"FIVE"`) normalised to
1-5 on the way in. **The code that exists does not do that.** The sample loader is:

```python
return min(max(int(raw), 1), 5) if raw.isdigit() else 1
```

Digits are clamped into 1-5; anything non-numeric — including `"FIVE"` — becomes **1**. There
is no string-enum mapping anywhere in the repository. This is only ever fed the assignment's
integer CSV, so it is currently inert, but a real Google integration would need the mapping
written.
