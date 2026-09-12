# Architecture

## What the product is

A Google Business Profile (GBP) management platform. A business connects their Google account once, and then manages every location they operate — profile details, hours, attributes, photos, posts, reviews — from one dashboard instead of Google's one-profile-at-a-time tools.

## The three objects that must stay separate

This separation is the backbone of the design. Merging any two of them breaks a required flow.

| Object | Answers | Google scope |
|---|---|---|
| **Identity** (`User`, `UserIdentity`) | Who is this person? | `openid email profile` |
| **Connection** (`GoogleConnection`) | Which Google account's profiles may we touch? | `business.manage` |
| **Project** (`Project`) | Which locations are we working on? | none — ours |

- One user → many connections.
- One connection → many projects.
- One location → many projects (`ProjectLocation` is many-to-many).

That last row is what makes "create a new project from an already-connected Google account, without reconnecting" possible.

## Flow

```
sign in (light scope)
   → name your organization
   → connect Google Business Profile (business.manage, separate consent)
   → discovery: ask Google what this account manages
   → review what was found, with per-location health status
   → select locations, name a project, import
   → background sync keeps a local copy current
   → manage from the dashboard; writes are previewed, approved, audited
```

## Why reads hit our database, not Google

Calling Google on every page load would be slow and would exhaust the per-minute quota. So a background worker syncs into Postgres and the UI reads locally. "Refresh" enqueues a job rather than blocking the request.

```
Google  →  sync worker  →  Postgres  →  API  →  UI
```

## Key decisions

### 1. Sign-in and Business Profile access are separate grants

`business.manage` is a Google-restricted scope requiring app verification. If it were bundled into the sign-in button, **nobody could log in** until Google approved the app. So sign-in asks only for `openid email profile`, and Business Profile access is requested later, inside the product, using incremental authorization (`include_granted_scopes=true`).

### 2. Everything Google goes through a provider abstraction

Google has not yet approved this app for API access — unapproved projects sit at **0 QPM** and every data call fails. Rather than block the build:

- `app/services/providers/fixture.py` — reads the 12 sample dental-clinic CSVs, so connect → discover → import works end to end today
- `app/services/providers/live.py` — the real Google calls
- `settings.gbp_provider` (`fixture` | `live`) selects one

Switching to real data is a one-line config change.

### 3. The schema models Google's shape, not the CSV's

The sample CSVs are a flattened simplification. Building to them would force a rewrite later:

- **Hours** are a list of periods, not one open/close per weekday — Google allows multiple periods per day and overnight spans where `close_day` differs from `open_day`.
- **Attributes** are typed (`BOOL` / `ENUM` / `REPEATED_ENUM` / `URL`) with JSON values, not scalar strings.
- **Media** is a list of items; any summary count is derived, never stored as source.
- **Star ratings** arrive as enum strings (`FIVE`), not integers.

### 4. Both Google ID forms are stored

The v1 APIs address a location as `locations/{id}`; the legacy v4 API needs `accounts/{account}/locations/{location}`. Reviews, posts and media are **still v4 only**. So `Location` carries `google_location_name`, `google_resource_name`, `place_id` and `store_code`.

### 5. Two retention zones

Google's API policy restricts how long API Content may be stored. So the schema separates:

- **Google Content** — raw profile text, reviews, media. Refreshable, treated as a cache.
- **Our data** — derived fields, projects, actions, audit records. Permanent, ours.

Needs legal review before any permanent data lake.

### 6. Every write is previewed, approved, and audited

No profile change is ever sent to Google without a person clicking approve. `locations.patch` supports `validateOnly=true`, so the user is shown exactly what will change and any field errors before anything is committed. Each attempt is recorded in `ProfileAction` with who, what, when, and Google's response.

## Backend layout

```
app/
  api/          routers only — thin, no business logic
  core/         config, database, security, crypto, oauth_state
  models/       one module per aggregate, re-exported from __init__
  schemas/      one module per domain, re-exported from __init__
  services/
    google/     oauth primitives, authed HTTP client, per-API modules
    providers/  GbpProvider protocol + fixture and live implementations
```

## Security notes

- Google refresh tokens are Fernet-encrypted at rest, never logged, never sent to the browser.
- The OAuth redirect round-trip is CSRF-protected by short-lived signed state tokens.
- ID tokens are verified against Google's JWKS with audience and issuer checked. An unverified `email_verified` claim is rejected — otherwise someone could claim an account by email.
- Disconnect revokes the grant at Google, not just locally. Deleting our row alone would leave the grant live.
- Every query is scoped to the caller's organization; out-of-organization resources return 404, not 403, so IDs are not enumerable.
