# Locus Intelligence API

FastAPI foundation for authentication and organization workspaces. The API uses
SQLAlchemy 2's async interface, PostgreSQL, Alembic migrations, Argon2 password
hashing, short-lived JWT access tokens, and rotating opaque refresh tokens stored
as SHA-256 digests.

## Local setup

Prerequisites: Python 3.12+, `uv`, and a running local PostgreSQL server.

```bash
createdb locus
cd backend
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

The default database URL uses the current operating-system user and PostgreSQL's
local Unix socket. Change `DATABASE_URL` in `.env` if your local server requires a
host, username, or password.

- API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/api/v1/health>

## API contract

- `POST /api/v1/auth/register` creates a user, organization, and owner membership.
- `POST /api/v1/auth/login` authenticates an existing user.
- `POST /api/v1/auth/refresh` rotates the HttpOnly refresh cookie and returns a new access token.
- `GET /api/v1/auth/me` requires `Authorization: Bearer <access-token>`.
- `POST /api/v1/auth/logout` revokes the refresh session and clears its cookie.

Registration and login responses include an access token. The browser sends that
token as a Bearer token. The longer-lived refresh credential is never exposed to
JavaScript: it is an HttpOnly, SameSite=Lax cookie scoped to authentication routes.
Set `COOKIE_SECURE=true` in HTTPS environments.

## Checks

```bash
uv run ruff check .
uv run pytest
uv run alembic current
```
