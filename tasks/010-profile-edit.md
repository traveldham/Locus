# 010 — Profile write path: preview, apply, audit

**Status:** BUILT (unverified against real Google) — 13 tests

## Goal

Make a business profile editable. This is the feature the whole product exists for — everything before it was a viewer.

## The safety model

Editing changes a real business's live listing on Google Search and Maps, and Google's policy requires the merchant's explicit consent for every change. So:

```
edit form  →  PREVIEW (dry run at Google, validateOnly=true)
           →  user sees exactly what changes, plus any field errors
           →  user confirms
           →  APPLY  →  ProfileAction records who, what, when, and Google's answer
```

Preview writes no audit row. Apply creates the `ProfileAction` **before** calling Google and transitions it `pending → executing → succeeded|failed`, so a crash mid-flight still leaves evidence.

## The data-loss guard (the most important detail here)

`locations.patch` requires an `updateMask`. **A patch without it is treated as a full replace that unsets every omitted field.** Get the mask wrong and you silently wipe a real business's phone number.

So the mask is derived server-side from `model_fields_set` **intersected with** "the value actually differs from the stored row":

- A field the client omits **cannot** enter the mask.
- A field resubmitted unchanged is dropped.
- A client-supplied mask is never trusted.

Text is compared blank-insensitively: `""` against a stored `None` is a no-op, while `""` against a real value is a genuine clear and is sent as an empty string. There is a test asserting an untouched field never appears in the mask.

## Field semantics

| Field group | Behaviour |
|---|---|
| Attributes | Diffed and written **per attribute** via `attributeMask`, so untouched attributes survive. When attributes change, `attributes` must also appear in `updateMask`. |
| Regular hours | Replaced wholesale — that is what `regularHours` does at Google. Special hours are left alone. |
| Text fields | Blank-insensitive comparison, as above. |

## Error codes

| Code | Meaning |
|---|---|
| 422 | Content rejected — field errors, from Google or from the local rules. Body carries `{message, field_errors}`. |
| 502 | Upstream unreachable or erroring. |
| 409 | The Google grant is dead; the user must reconnect. |

All three write a `failed` `ProfileAction` and leave the local `Location` untouched. The local row is only updated **after** Google confirms, so our copy never drifts ahead of the truth.

## Judgment calls worth keeping

- **Validation runs locally first**, before any network call, so a doomed edit does not consume one of the ten per-minute edit slots Google allows per profile.
- A **per-profile 10-edits-per-minute limiter** refuses locally rather than bursting into a quota rejection.
- `valid` in the preview is true only when there is something to send *and* the dry run passed — so an empty diff reads as "not applicable", not "ready to go".
- `patch_json()` was added to the Google client returning `(status, body)` rather than raising, because the error body is where the per-field reasons live. Raising would throw away exactly the information the user needs.
- Hours use targeted `remove()` + `flush()` before re-insert, deliberately avoiding `.clear()` — see the `MissingGreenlet` trap in `003-gbp-connection-discovery-import.md`.

## Endpoints

| Method | Path |
|---|---|
| POST | `/locations/{id}/edits/preview` |
| POST | `/locations/{id}/edits` |
| GET | `/locations/{id}/actions` |

## Verification

13 tests: mask contains only genuinely changed fields; empty diff yields an empty mask and apply 422s; **an untouched field never enters the mask**; invalid input surfaces `field_errors` without applying; success writes a `succeeded` action and updates the local row; failure writes a `failed` action and leaves the row unchanged; audit history is newest-first; cross-organization access 404s; plus the live JSON mapping and Google error-body parsing.

**Not verified:** no real `locations.patch` has been sent. Blocked on API approval.
