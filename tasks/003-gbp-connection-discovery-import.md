# 003 — GBP connect, provider abstraction, discovery, import

**Status:** BUILT (unverified against real Google)

## Goal

The heart of the product:

> Connect the Google account → ask Google which locations it manages → show everything found with each one's health → select some → import into a named Project.

## The constraint that shapes the design

Google has **not approved this app** for Business Profile API access. Unapproved Cloud projects sit at **0 QPM** and every data call fails. Approval takes weeks.

So all Google data goes through a provider abstraction:

| Implementation | Behaviour |
|---|---|
| `providers/fixture.py` | Reads the 12 sample dental-clinic CSVs in `locus-intelligence-assignment/data/`. Uses the real `gbp_location_id` column, and deliberately leaves some locations with empty description/website so "incomplete profile" is genuinely represented. |
| `providers/live.py` | Calls Account Management v1 and Business Information v1 for real. |

`settings.gbp_provider` (`fixture` | `live`) selects one. **Switching to real data is a one-line config change** and nothing downstream knows the difference.

Provider methods return provider-neutral frozen dataclasses, never raw Google JSON, so the rest of the codebase never couples to Google's response shape.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/integrations/google` | Connection status for the org |
| GET | `/api/v1/integrations/google/authorize` | Consent URL — **`offline=True`** |
| GET | `/api/v1/integrations/google/callback` | 302 back to `/settings/integrations?connected=1` |
| GET | `/api/v1/integrations/google/discovery` | What Google sees — does **not** persist locations |
| POST | `/api/v1/integrations/google/import` | Persists selected locations, creates the Project |
| DELETE | `/api/v1/integrations/google` | Disconnect — **revokes at Google** |

## Gotchas that cost time if missed

- **`offline=True` forces `prompt=consent`.** Google returns a refresh token only on a fresh consent. A returning user who re-authorises without it yields *no refresh token*, and background sync silently breaks later, far from the cause.
- **`readMask` is a REQUIRED query parameter** on every Business Information read. Omitting it is an error, not a default.
- **Discovery must not persist locations.** It is a preview. Only import writes `Location` rows.
- **Import must be idempotent.** Unique on `(organization_id, google_location_name)`, so re-importing updates rather than duplicating.
- **Disconnect must call `revoke_token`.** Deleting our row alone leaves the grant live on the user's Google account.
- **`invalid_grant`** means the user revoked access at Google — mark the connection `needs_reauth` rather than retrying forever.

## `missing_fields`

Computed during discovery by checking description, website, phone, primary category, regular hours and address. Drives the "Incomplete" chip in the UI. This is descriptive, not a recommendation — it reports what is empty, it does not score anything.

## Decisions made during the build

- **Fixture connections are auto-provisioned.** `business.manage` consent is unusable until Google approves the app, but `ExternalAccount`, `SyncRun` and `Location` all require a `GoogleConnection`. In fixture mode `ensure_connection()` mints a local stand-in (`google_subject` = `fixture:<org>`); in live mode a real grant is required or it returns 409. Gated on `provider.name != "fixture"`, so the shortcut cannot leak into live mode. A real callback deletes the stand-in for that org.
- **Import reuses a project with the same name** within the organization rather than creating `texas-clinics-2`. This is what makes retrying the wizard genuinely safe; slugs stay unique per org.
- **Disconnect deletes the connection row** after revoking at Google, so the encrypted refresh token does not sit at rest. `locations.connection_id` is nulled explicitly (SQLite does not enforce the FK), so **imported locations and projects survive a disconnect** — the UI dialog now states this.
- **Callback identity is best-effort.** If the `id_token` is absent or fails verification, it falls back to a stable `google-connect:<org>` subject with a blank email rather than failing the whole connect.
- Provider and quota failures map to **502**, `needs_reauth` to **409** — never a 500. Today's expected path is a 403/quota error, and it must read as an upstream condition, not a crash.

## Trap worth remembering

Calling `.clear()` on an **unloaded** relationship collection of a pending object does not mark it loaded, so a later `flush()` turns the next access into a lazy load and raises `MissingGreenlet`. `upsert_location` therefore only clears children on the existing-row path, where they were `selectinload`ed, with an intermediate flush ordering the DELETEs before the re-INSERTs so the `(location_id, attribute_id)` unique constraint holds.

## Verification

6 tests using the fixture provider: auth required, status when unconnected, discovery returning the 12 fixture locations with `missing_fields` populated, import creating a project with the right count, and **importing twice being idempotent**.

**Not verified:** the live provider has never successfully called Google. Expected to return 403/quota until approval — that path is handled as a 502, not a crash.
