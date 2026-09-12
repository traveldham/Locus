# 011 — Reviews: model, provider, reply API

**Status:** BUILT (unverified against real Google) — 10 tests

## Goal

Every Google review across every location in one inbox, with replies. For most customers of a product like this, it is the reason they log in daily.

## The API fact that dictates the implementation

Reviews and replies are **still only on the legacy v4 API**:

```
GET    https://mybusiness.googleapis.com/v4/accounts/{a}/locations/{l}/reviews
PUT    .../reviews/{reviewId}/reply
DELETE .../reviews/{reviewId}/reply
```

That path needs the **`accounts/{a}/locations/{l}`** form stored on `Location.google_resource_name` — *not* `google_location_name`, which holds the v1 `locations/{id}` form. Using the wrong one is the single most likely bug in this area, which is why both forms are stored on the model.

A location with a blank `google_resource_name` cannot have its reviews fetched. Sync reports that location in a `skipped` list rather than silently returning nothing — a silent empty result here looks identical to "this location has no reviews", which is a bad failure to debug.

`starRating` also arrives as an enum **string** (`"FIVE"`), not an integer, and is mapped to 1–5 on the way in.

## Model

One `Review` row per review, with the owner's reply **inline** (`reply_comment`, `reply_update_time`) rather than in a separate table — Google returns `reviewReply` nested and there is at most one, so a join would buy nothing. Unique on `(location_id, google_review_id)`, indexed on `(location_id, create_time)` for inbox ordering.

Migration: `20260913_0003`, on top of `20260913_0002`.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/reviews` | Filters: `project_id`, `location_id`, `rating`, `replied`, `q`. Newest first, cap 200. |
| GET | `/reviews/{id}` | |
| PUT | `/reviews/{id}/reply` | Create or update the owner reply |
| DELETE | `/reviews/{id}/reply` | Remove the owner reply only |
| POST | `/reviews/sync` | Upserts from the provider, records a `SyncRun` |

## A reply is a public write, so it is audited

Replying publishes text on a real business's public Google listing. Every reply and delete creates a `ProfileAction` (`reply_to_review` / `delete_review_reply`), transitions `pending → executing → succeeded|failed`, and only updates the local `Review` after the provider confirms. Upstream failures return **502**, never 500.

## What deliberately does not exist

**There is no review-delete endpoint, and there must never be one.** Google provides no way to delete a customer's review — only the owner's reply can be removed. Flagging a review is Google's own UI. Any control implying otherwise would be lying to the user about what the product can do.

## Verification

10 tests on the fixture provider (1,514 sample reviews joined with 874 replies): auth required, sync imports and is idempotent on a second run, filtering by rating / replied / location, pagination and the cap, reply creating a `ProfileAction` and setting the comment, delete clearing it, cross-organization access returning 404, and `"FIVE"` mapping to 5.

**Not verified:** no real v4 call has been made. Blocked on API approval.

## Coupling to watch

`reviews_connection` reuses `ensure_connection` from the integrations router so fixture mode shares one stand-in connection instead of minting a conflicting second one. If that function is ever renamed, this import is the single coupling point.
