# Editing a profile

Two endpoints, one flow: **preview → consent → apply**. Nothing is written to our database
until the provider confirms the write.

```
POST /locations/{id}/edits/preview     plan_edit  →  provider.update_location(validate_only=True)
                                       returns: changes, update_mask, field_errors, valid
        │  the operator reads it and confirms
        ▼
POST /locations/{id}/edits             plan_edit  →  ProfileAction(pending)  [committed]
                                                  →  ProfileAction(executing)
                                                  →  provider.update_location(validate_only=False)
                                                  →  apply_locally(...)      [only now]
                                                  →  ProfileAction(succeeded)
```

## Why the client never sends an update mask

`locations.patch` treats **any field omitted from the mask as unset**. A client-supplied
mask naming a field the operator did not touch would silently wipe that field on a live
public business listing.

So the mask is derived from a real diff, server-side, every time. `build_update_mask` maps
our field names to Google's field paths in one fixed order, so a preview, an audit row and
the request actually sent to Google always read the same:

| Our field | Google mask path |
| --- | --- |
| `title` | `title` |
| `phone_primary` | `phoneNumbers` |
| `website_uri` | `websiteUri` |
| `description` | `profile` |
| `open_status` | `openInfo` |
| `hours_periods` | `regularHours` |
| `attributes` | `attributes` |
| `primary_category` | `categories` |

A collection field contributes exactly one path however many members it carries.

## Omitted is not null

`LocationEditRequest` has eight optional fields, all defaulting to `None`. `plan_edit`
decides what changed from `payload.model_fields_set` — the fields **explicitly present on
the request** — not from whether the value is `None`.

This matters because Pydantic marks a field as set when it is passed to the constructor
*even if the value is `None`*. A caller that fills in every field in the schema and sends
`null` for the ones it did not mean to change would, unfiltered, arrive at Google as
"change the phone number **and blank the title, website and description**".

| Shape | Meaning |
| --- | --- |
| field omitted | untouched — stays out of the mask |
| `"value"` | set it |
| `""` (text fields) | **clear it** — sent to Google as `""`, stored locally as `None` |
| `null` | for text fields, treated as a clear; for `hours_periods`, a no-op |

## The diff, field by field

- **Text fields** (`title`, `phone_primary`, `website_uri`, `description`): compared after
  stripping, with `""` mapped to `None` — blank and absent are the same thing. A genuine
  clear is sent as `""`, because `None` would read as "untouched" downstream.
- **`open_status`**: compared to the stored enum.
- **`hours_periods`**: compared as sorted 6-tuples against the stored **regular** periods
  only. Sending it replaces the whole regular schedule.
- **`attributes`**: a **merge**, not a replace. Only attributes whose
  `(value_type, values)` genuinely differ are sent; the rest of the location's attributes
  are untouched, because `attributeMask` names exactly the ones written.
- **`primary_category`**: compared on `category_name` only. The display name is Google's
  own rendering, so a differing label alone is not a change worth sending.

## Validation

`validate_changes` returns errors keyed by **our** field name — the shape the UI renders.
The exact rules:

| Field | Rule | Message |
| --- | --- | --- |
| `title` | non-blank, ≤320 chars | "Business name is required." / "Business name must be 320 characters or fewer." |
| `phone_primary` | ≥7 digits after stripping non-digits (a clear is allowed) | "Enter a phone number with at least 7 digits." |
| `website_uri` | `http`/`https` scheme **and** a host | "Enter a full website address starting with http:// or https://." |
| `description` | ≤750 chars | "Description must be 750 characters or fewer." |
| `hours_periods` | weekday names; open 00:00-23:59; close 00:00-**24:00** | see below |
| `attributes` | non-blank id and value type | "Every attribute needs an identifier." |
| `primary_category` | non-blank category name | "Choose a primary category." |

Hours are checked per period and **stop at the first error**, so at most one message
appears under `hours_periods`. Google writes a period ending at midnight as `24:00`, so
`24` is allowed on close only — and only with zero minutes. An overnight span
(`open_day != close_day`) is valid; on the same day, close must be after open.

## What preview does and does not do

- If the plan is empty, preview returns `{changes: [], update_mask: [], field_errors: {},
  valid: false}` **immediately** — the provider is never called, and a Google connection is
  not required.
- Otherwise it calls `provider.update_location(..., validate_only=True)`, the identical
  request, which reports the same field errors without committing anything.
- **No `ProfileAction` row is written and the stored `Location` is untouched.**
- `valid` is true only when there was something to send *and* the provider accepted it.

## What apply does

1. `owned_location` — 404 if not yours.
2. `plan_edit`; an empty plan is a **422** with *"Nothing to update — the submitted values
   match the current profile."* and **no audit row**.
3. `edit_connection` — the location's own connection, else the organization's most recent;
   **409 "Connect a Google account first"** if there is none.
4. Write `ProfileAction(status=pending)` and **commit it before calling the provider**, so
   a crash mid-call still leaves the attempt recorded.
5. Flip to `executing`, commit.
6. Call the provider with `validate_only=False`.

Failure paths, all of which leave the stored `Location` unchanged:

| What happened | Action row | HTTP |
| --- | --- | --- |
| `ProviderError` | `failed`, `error` set | **502**, detail is the message |
| Rejected with field errors | `failed`, `google_response` stored | **422**, detail is `{message, field_errors}` — an object |
| Rejected without field errors | `failed` | **502** |

On success: `apply_locally` mirrors the change into our copy, the action becomes
`succeeded`, and `google_response` records the reply. **The local copy moves only after
the provider confirms.**

## Mirroring locally

`apply_locally` is documented as *"Mirror a confirmed Google write into our copy. Never
call before Google says ok."*

- Text fields are stored stripped, with `""` becoming `None`.
- `primary_category` mutates the existing `is_primary` row, or appends one.
- `hours_periods` deletes every `REGULAR` row, **flushes** so the DELETEs are ordered before
  the re-INSERTs, then extends. Non-regular sets survive.
- `attributes` merge by `attribute_id`.

## What cannot be edited here

Not in `EDITABLE_FIELDS`, so no path writes them: `google_location_name`,
`google_resource_name`, `source_location_id`, `place_id`, `store_code`, the whole address
(`address_lines`, `locality`, `administrative_area`, `postal_code`, `region_code`),
`latitude`/`longitude`, `opening_date`, `maps_uri`, `new_review_uri`, `source`,
`last_synced_at`, the Google state booleans, and **secondary categories** — only
`is_primary=True` is ever written.

Two more that surprise people:

- **`open_status` cannot be cleared.** Sending `"open_status": null` produces a
  `FieldChange` but no mask entry, so an otherwise-empty plan is still "empty": preview
  returns the empty response and apply returns 422.
- **An attribute cannot be deleted**, only set or changed.

## The audit trail

Every write writes a `ProfileAction` first:

| Column | Holds |
| --- | --- |
| `action_type` | `location_update` |
| `user_id` | who did it — `ON DELETE SET NULL`, so the trail outlives the user |
| `payload` | `{"update_mask": [...Google paths...], "changes": [{field, label, current, proposed}, ...]}` |
| `status` | `pending → executing → succeeded \| failed` |
| `google_response` | the provider's reply and any field errors (not exposed by the API) |
| `error` | the failure sentence |

`GET /locations/{id}/actions` returns them newest first. Note it is **not filtered by
action type**, so review replies (`reply_to_review`, `delete_review_reply`) appear in a
profile's change history too — they are writes against the same location.

`ActionStatus` declares `approved`, but nothing in the codebase assigns it; it appears to
be reserved for a planned approval step.

## Known frontend gaps

Real, verified, and worth fixing:

1. `ProfileActionResponse.user` is an object `{id, email, full_name}`, but the TypeScript
   client types it as `string | null` and interpolates it into a template literal.
2. The change-history summary iterates `payload.update_mask` (Google paths like
   `phoneNumbers`) and then looks those keys up in `payload`, where they do not exist — so
   every value renders as "—" and the label falls through to "Phonenumbers". The real
   before/after data sits unread in `payload.changes`.
3. The hours error is set under the key `hours_periods` but cleared under `hours`, so
   editing an hours row does not clear the banner.
4. The form cannot edit attributes or the primary category at all; only the audit
   suggestion panel sends `attributes` — and it applies **without a preview step**.
