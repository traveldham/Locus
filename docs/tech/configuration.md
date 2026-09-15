# Configuration

Backend settings are a pydantic-settings `Settings` class read from `backend/.env` and the
environment. **Env var names are the upper-case field names.** Unknown keys are ignored.

## Every setting

| Variable | Default | Controls |
| --- | --- | --- |
| `APP_NAME` | `Locus Intelligence API` | FastAPI title |
| `APP_ENV` | `development` | In `development`, a 500 returns the real exception string; anything else returns "Internal server error" |
| `API_PREFIX` | `/api/v1` | Router mount prefix **and** the refresh-cookie path |
| `DATABASE_URL` | `postgresql+asyncpg:///locus` | A bare `postgresql://` is rewritten to `+asyncpg` automatically |
| `SECRET_KEY` | a development placeholder | JWT signing. **Minimum 32 characters.** Change it |
| `FRONTEND_URL` | `http://localhost:3000` | The single entry of the CORS allow-list |
| `ACCESS_TOKEN_MINUTES` | `15` | Access-JWT lifetime |
| `REFRESH_TOKEN_DAYS` | `30` | Refresh-session lifetime and cookie max-age |
| `COOKIE_SECURE` | `false` | **Set `true` behind HTTPS** |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker, result backend, agent pub/sub |
| `CELERY_ALWAYS_EAGER` | `false` | Run tasks inline in the calling process — no worker needed |
| `AUDIT_JOB_TIMEOUT_SECONDS` | `900` | 30-7200. Celery-wide time limit |
| `AGENT_TURN_TIMEOUT_SECONDS` | `180` | 30-600. Per-task limit on an agent turn |
| `DB_POOL_SIZE` | `10` | 1-100 |
| `DB_MAX_OVERFLOW` | `20` | 0-100 |
| `SAMPLE_DATA_DIR` | unset | Directory of the sample CSVs. Blank falls back to `<repo>/locus-intelligence-assignment/data` |
| `SUGGESTIONS_ENABLED` | `true` | Whether the audit drafts suggestions at all |
| `SUGGESTIONS_TIMEOUT_SECONDS` | `60` | 5-300 |
| `LLM_PROVIDER` | `vertex` | `vertex` or `gemini` |
| `VERTEX_PROJECT` | unset | **Required** for Vertex |
| `VERTEX_LOCATION` | `global` | |
| `VERTEX_MODEL` | `gemini-3.8-flash` | |
| `GEMINI_API_KEY` | unset | Required when `LLM_PROVIDER=gemini` |
| `GEMINI_MODEL` | `gemini-3.8-flash` | |

`.env.example` does not list `APP_NAME`, `API_PREFIX`, `AUDIT_JOB_TIMEOUT_SECONDS`,
`AGENT_TURN_TIMEOUT_SECONDS` or `SUGGESTIONS_TIMEOUT_SECONDS`, though all five are valid.

## Frontend

One variable, in `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

It must include the `/api/v1` suffix — the client appends bare paths like `/locations` to it.

## Minimum for production

```
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://user:pass@host/locus
SECRET_KEY=<32+ random characters>
FRONTEND_URL=https://your.domain
COOKIE_SECURE=true
REDIS_URL=redis://localhost:6379/0
LLM_PROVIDER=vertex
VERTEX_PROJECT=<your GCP project>
```

`SECRET_KEY` and `COOKIE_SECURE` are the two that actually matter for safety. The default
secret is a visible placeholder, and leaving `COOKIE_SECURE=false` behind HTTPS sends the
refresh cookie over plaintext on any downgrade.
