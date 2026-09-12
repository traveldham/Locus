# 001 — Backend data foundation

**Status:** DONE · verified 2026-09-12

## Goal

Lay the complete data foundation for the GBP platform, and restructure the two monolithic modules into proper packages so parallel work does not collide.

## Scope

- `app/models.py` → `app/models/` package (`base`, `user`, `organization`, `connection`, `location`, `project`, `sync`, `audit`), re-exported from `__init__` so existing imports are unchanged.
- `app/schemas.py` → `app/schemas/` package (`common`, `auth`, `integrations`, `projects`, `locations`).
- `app/core/crypto.py` — Fernet encryption for Google refresh tokens at rest.
- `app/core/oauth_state.py` — short-lived signed state tokens, CSRF protection for the OAuth redirect round-trip.
- Config: Google credentials, both redirect URIs, encryption key, `gbp_provider`.
- One Alembic migration.

## Tables added (11)

`user_identities` · `google_connections` · `external_accounts` · `locations` · `location_categories` · `location_hours_periods` · `location_attribute_values` · `projects` · `project_locations` · `sync_runs` · `profile_actions`

Plus: `users.password_hash` altered to **nullable** — Google-only accounts have no password.

## Decisions worth remembering

- **Hours are periods, not weekdays.** `location_hours_periods` stores `open_day`/`close_day` separately so multiple periods per day and overnight spans both work. Collapsing to one row per weekday would have to be undone later.
- **Attributes are typed.** `value_type` plus a JSON `values` list, because Google attributes are `BOOL` / `ENUM` / `REPEATED_ENUM` / `URL`. A scalar string column cannot represent them.
- **Both Google ID forms are stored.** `google_location_name` (`locations/{id}`) for the v1 APIs, `google_resource_name` (`accounts/{a}/locations/{l}`) for the legacy v4 APIs that still own reviews, posts and media.
- **`ProfileAction` exists from day one.** Every write we ever send to Google gets a row first. Retrofitting an audit trail after the fact is much harder.
- **`ProjectLocation` is many-to-many.** Required for "new project from an existing connection".

## Gotcha

`google-auth` was added for ID-token verification, then removed — its verifier hard-requires the `requests` library, and PyJWT (already a dependency) does JWKS verification natively. Avoided pulling in a second HTTP stack.

## Verification

```bash
cd backend
uv run ruff check . && uv run ruff format --check .
uv run pytest
uv run python -c "from app.core.database import Base; import app.models; print(len(Base.metadata.tables))"   # 15
```

Confirmed: 15 tables on the metadata, `password_hash` nullable, crypto round-trips, OAuth state issue/consume works including wrong-purpose rejection, migration head `20260913_0002`.

**Not verified:** the migration has never been run against Postgres. No database was available and starting servers is out of scope. First `alembic upgrade head` is still an unexercised path.
