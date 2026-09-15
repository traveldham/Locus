# Connection, provider and sync

How a location gets into the database, and what the "Google connection" actually is.

## The Google connection

`google_connections`, unique on `(organization_id, google_subject)`.

It exists so the integrations screen can show the product as connected, and so an edit can
be attributed to a connection. **Nothing in the application calls Google.** The seed writes
one row with an obvious non-secret placeholder in `refresh_token_encrypted` — the column is
`NOT NULL` and there is no credential to put in it:

```
google_account_email  the demo account
google_subject        "demo-connection"
refresh_token_encrypted  "demo-connection"    ← deliberately not a secret
scopes                https://www.googleapis.com/auth/business.manage
status                active
```

`ConnectionStatus` is `active | needs_reauth | revoked | error`.

`ExternalAccount` hangs off it — a Google Business Profile account (`accounts/123456`)
reachable through the connection. The sample provider returns exactly one:

```
resource_name       accounts/100000000000000000001
account_name        Brightpath Dental Group
account_type        LOCATION_GROUP
role                PRIMARY_OWNER
verification_state  VERIFIED
```

`GET /api/v1/integrations/google` returns the connection or `null`.

Editing requires one: `edit_connection` prefers the location's own `connection_id`, falls
back to the organization's most recently created connection, and raises
**409 "Connect a Google account first"** if there is none.

## The provider abstraction

```python
class GbpProvider(Protocol):
    name: str
    location_source: LocationSource
    async def list_accounts(connection) -> list[ProviderAccount]
    async def list_locations(connection, account_resource_name) -> list[ProviderLocation]
    async def update_location(connection, location, changes, *, validate_only) -> UpdateResult
```

`get_provider()` returns `SampleGbpProvider()` **unconditionally** — no env var, no registry,
no switch. The module says why:

> Google never approved this Cloud project for Business Profile API access — every live read
> came back `429 RESOURCE_EXHAUSTED` with `quota_limit_value: 0` — so the live implementation
> has been removed rather than kept as code that cannot run.

A test asserts it: `isinstance(get_provider(), SampleGbpProvider)` and
`provider.location_source is LocationSource.fixture`.

### What the sample provider does

- `list_accounts` returns the one account above.
- `list_locations` parses `locations.csv`, `location_hours.csv`, `location_attributes.csv`
  and `attribute_catalog.csv` into `ProviderLocation` objects, then replays any in-process
  edits over them.
- `update_location` builds the real mask, runs the real `validate_changes`, and — only when
  `validate_only=False` — records the change in a **module-level dict** keyed by
  `google_location_name`. That is a demo of the round trip, not a second database; it is
  process-local and cleared by `forget_edits()`.

Deliberate honesty in the sample data: no street line is invented (the CSV has only the
town), and blank `website_url` / `description` stay blank. Inventing a street would make the
"Incomplete address" finding lie.

### Reviews use a different provider

Reviews were never migrated to the split v1 services and are **still v4 only**, addressed by
`Location.google_resource_name` (`accounts/{a}/locations/{l}`) rather than
`google_location_name`. So `app/services/providers/reviews.py` is a separate protocol with
its own `SampleReviewsProvider` and its own `get_reviews_provider()`.

`account_qualified_name(location)` raises `ProviderError` when `google_resource_name` is
blank — rather than quietly returning an empty inbox.

A reply written in process is kept in a module-level dict where `None` records a **deleted**
reply, which is different from never having had one.

## How a location arrives

Only `app/seed.py` calls the sync helpers. The HTTP API never does.

```
SampleGbpProvider.list_accounts   →  upsert_external_accounts
SampleGbpProvider.list_locations  →  upsert_location  (one per location)
                                  →  link_locations_to_project
```

**`upsert_location`** keys on `(organization_id, google_location_name)` and then overwrites
**every** scalar column from the payload, plus `connection_id`, `external_account_id`,
`source` and `last_synced_at`. Children — categories, hours, attributes — are **replaced
wholesale**: cleared, flushed (so the DELETEs are ordered before the re-INSERTs, keeping the
`(location_id, attribute_id)` unique constraint happy), then re-inserted. Attributes are
de-duplicated on the way in, first occurrence winning.

Two consequences worth stating plainly:

- **A resync discards any local edit not present in the provider payload.** That is correct
  for a mirror, and it is why edits go to the provider first.
- A brand-new location skips the clear step, because clearing would leave the collections
  unloaded and trip a lazy load after the flush.

**`upsert_external_accounts`** keys on `resource_name` within the connection and never
deletes. **`link_locations_to_project`** adds missing links and **never unlinks**.

## Sync runs

`sync_runs` records one execution of a background pull: `kind`
(`discovery | location_profile | reviews | performance | media | posts`), `status`
(`pending | running | succeeded | failed`), `started_at`, `finished_at`, `records_written`,
`error`.

Two things write one today: `POST /api/v1/reviews/sync` (kind `reviews`) and
`POST /api/v1/insights/load-sample-data` (kind `performance`). A failure leaves the error
text behind rather than vanishing.

## When Google approves access

The change is narrow, and that is the point of the seam:

1. Implement `GbpProvider` against the Business Information API.
2. Return it from `get_provider()`.
3. Implement `ReviewsProvider` against the v4 reviews API; return it from
   `get_reviews_provider()`.
4. Give the connection a real refresh token and restore the OAuth flow.

Nothing in `app/api/locations.py`, `location_edits.py` or the agent changes at all.

## Related

- [overview.md](overview.md) · [editing-a-profile.md](editing-a-profile.md)
- [../../architecture/provenance.md](../../architecture/provenance.md) — how a row says where it came from
