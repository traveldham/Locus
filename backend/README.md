# Locus Intelligence API

FastAPI backend for the Google Business Profile (GBP) management platform. Uses
SQLAlchemy 2's async interface, PostgreSQL, Alembic migrations, Argon2 password
hashing, short-lived JWT access tokens, and rotating opaque refresh tokens stored
as SHA-256 digests.

The app ships a single pre-seeded demo account: there is no registration and no
live Google connection.

## Local setup

Prerequisites: Python 3.12+, `uv`, and a running local PostgreSQL server.

```bash
createdb locus
cd backend
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000
```

The default database URL uses the current operating-system user and PostgreSQL's
local Unix socket. Change `DATABASE_URL` in `.env` if your local server requires a
host, username, or password.

## Seeding the demo world

```bash
uv run python -m app.seed
```

Demo credentials:

| Field | Value |
| --- | --- |
| Email | `pawanpatrapp@gmail.com` |
| Password | `Pawan 2000` |

`app/seed.py` builds everything the UI needs from the sample CSVs in
`../locus-intelligence-assignment/data` (override with `SAMPLE_DATA_DIR`): the
user above, the "Brightpath Dental Group" organization it owns, a Google
connection row, the sample external account, all 12 locations with their hours,
categories and attributes, a project holding all 12, all 1,514 reviews with their
874 owner replies, and ~8,864 rows of daily performance, search terms, media,
posts, bookings, tracked keywords, weekly ranks and competitor observations.

Every write is an upsert on a natural key, so the command is safe to run
repeatedly — it refreshes the demo world rather than duplicating it. It prints a
per-table summary, and fails with a message naming the path if the CSV directory
is missing.

## Google Business Profile data

Google never approved this Cloud project for Business Profile API access: live
reads returned `429 RESOURCE_EXHAUSTED` with `"quota_limit_value": "0"`, because
unapproved projects have a quota of zero. The OAuth flows and the live API client
have therefore been removed rather than kept as code that cannot run.

Everything is served from the sample dataset through the same provider interface
the live APIs would have used, and the app stays honest about that: locations are
stored with `source = fixture`, the API returns that on every location, and the UI
labels them "Sample data".

The seeded `GoogleConnection` row is what makes the integrations screen show the
account as connected. Its refresh-token column holds the literal placeholder
`demo-connection`, not a credential — nothing in the application calls Google.

## API contract

- `POST /api/v1/auth/login` authenticates the seeded user.
- `POST /api/v1/auth/refresh` rotates the HttpOnly refresh cookie and returns a new access token.
- `GET /api/v1/auth/me` requires `Authorization: Bearer <access-token>`; it returns the user and its organization.
- `POST /api/v1/auth/logout` revokes the refresh session and clears its cookie.
- `GET /api/v1/integrations/google` returns the seeded connection.

Login and refresh responses include an access token. The browser sends that token
as a Bearer token. The longer-lived refresh credential is never exposed to
JavaScript: it is an HttpOnly, SameSite=Lax cookie scoped to authentication routes.
Set `COOKIE_SECURE=true` in HTTPS environments.

`POST /api/v1/reviews/sync` records what it did in `sync_runs`, so a failure
leaves the error text behind instead of disappearing.

- API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/api/v1/health>

## Checks

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
uv run alembic current
```
