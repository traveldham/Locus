# Google Business Profile management

The core of the product: mirror a Google Business Profile into our database, show it the
way a customer sees it, and let an operator change it — with a preview, a consent step and
an audit trail on every write.

Code: `backend/app/api/locations.py`, `backend/app/services/location_edits.py`,
`backend/app/services/gbp_sync.py`, `backend/app/services/providers/`.
Screens: `frontend/src/components/locations/`.

## The honest state of it

**Nothing here talks to Google.** Google never approved this Cloud project for Business
Profile API access — every live read came back `429 RESOURCE_EXHAUSTED` with
`quota_limit_value: 0` — so the live implementation was **removed** rather than kept as
code that cannot run. What remains is a provider abstraction with one implementation,
`SampleGbpProvider`, which reads the assignment's CSVs and records writes in process
memory.

```python
def get_provider() -> GbpProvider:
    """The Business Profile provider. There is only one, and it reads the sample CSVs."""
    return SampleGbpProvider()
```

That is the single seam. The edit path — plan, validate, preview with `validateOnly=true`,
consent, apply, mirror locally, audit — is real and complete, and it builds a genuine
Google `updateMask`. When quota is granted, `get_provider()` is the one function that
changes.

Every row the sample provider produces is stamped `Location.source = fixture`, and the UI
labels it "Sample data" on every row and suppresses affordances that would lie (the
"Directions" link on the profile preview, for instance).

## What a location is

One row in `locations`, unique on `(organization_id, google_location_name)`, with three
child collections — `categories`, `hours_periods`, `attributes` — all cascade-deleted.

Both Google identity forms are kept, because the APIs disagree:

| Column | Example | Used by |
| --- | --- | --- |
| `google_location_name` | `locations/123` | v1 Business Information API; our natural key |
| `google_resource_name` | `accounts/1/locations/123` | the legacy v4 API — which reviews still need |
| `source_location_id` | `LOC-001` | the assignment dataset's own join key |

`LocationSource` is `google | fixture | manual`. `OpenStatus` is
`open | closed_temporarily | closed_permanently`.

## The endpoints

All under `/api/v1`.

| Method | Path | Returns |
| --- | --- | --- |
| `GET` | `/locations` | `list[LocationSummary]` — a bare array, not an envelope |
| `GET` | `/locations/attribute-catalog` | The organization's attribute vocabulary |
| `GET` | `/locations/{id}` | `LocationDetail` — every field, plus categories, hours, attributes |
| `POST` | `/locations/{id}/edits/preview` | `EditPreviewResponse` — what would change, and whether Google accepts it |
| `POST` | `/locations/{id}/edits` | `201` `ProfileActionResponse` — the audit row for the write |
| `GET` | `/locations/{id}/actions` | `list[ProfileActionResponse]` — change history |

`GET /locations` takes `project_id`, `q`, `limit` (1-200, default 50) and `offset`. Search
is an escaped `ILIKE` across exactly three columns — `title`, `store_code`, `locality`.
Because wildcards are escaped, `q=%` matches nothing rather than everything. Ordering is
`title, id`.

A cross-tenant id is always a **404**, never a 403 — `owned_location` filters on
`organization_id` in the same query that fetches the row, so "not yours" and "not there"
are indistinguishable from outside.

Route order matters: `/attribute-catalog` is declared *before* `/{location_id}`, or it
would be parsed as a UUID.

## Reading it back

`LocationSummary` is the list shape: identity, title, store code, primary category,
a single-line `address`, locality, open status, the four Google state flags
(`has_voice_of_merchant`, `has_pending_edits`, `has_google_updated`, `is_duplicate`),
`source` and `last_synced_at`.

`address` is not a column. `build_address` joins `address_lines`, `locality`,
`administrative_area`, `postal_code` with `", "`, dropping blanks. **`region_code` is
deliberately not part of it.**

`LocationDetail` adds the rest of the columns plus the three child collections.

## Related

- [editing-a-profile.md](editing-a-profile.md) — plan, preview, consent, apply, audit
- [hours-categories-attributes.md](hours-categories-attributes.md) — the three child collections and their rules
- [connection-and-sync.md](connection-and-sync.md) — the provider, the Google connection, and how a location gets here
- [../ai-agent/overview.md](../ai-agent/overview.md) — the agent edits profiles through this same path
