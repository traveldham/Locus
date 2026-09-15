# Tech overview

Everything that runs, what it is written in, and what talks to what.

## The stack

| Layer | Choice | Version |
| --- | --- | --- |
| Backend | **FastAPI** + Pydantic v2 | Python ≥3.12, managed with **uv** |
| ORM | SQLAlchemy 2.0 async + Alembic | asyncpg driver |
| Database | **PostgreSQL** | SQLite (aiosqlite) in tests |
| Background work | **Celery** + **Redis** | Redis is broker, result backend and the agent's pub/sub |
| AI | **Vertex AI**, Gemini (`gemini-3.8-flash`) | via `langchain-google-vertexai` + LangGraph |
| Frontend | **Next.js 16** App Router, React 19, TypeScript | |
| Data fetching | **TanStack Query v5** | no Redux |
| Styling | **Tailwind CSS v4** | configured in CSS — there is no `tailwind.config` |
| Charts | Recharts | |
| Serving | uvicorn + `next start` behind **nginx**, systemd units | |

## Four processes

```
nginx  :80/:443
  ├── /api/v1/agent/turns/*/stream   → uvicorn, buffering OFF   (SSE)
  ├── /api/                          → uvicorn  :8000
  └── /                              → next start :3000

uvicorn        app.main:app          the API
celery worker  -A app.worker         audits and agent turns
next start                           the UI
postgres + redis                     state and the broker
```

`locus-backend`, `locus-celery` and `locus-frontend` are the three systemd units.

## What runs in the background, and why

Two things cannot sit inside an HTTP request:

**An audit.** One request fans out to six workers, each reading a snapshot of the profile and
running its category's checks, then a finish step assembles and scores. Celery task names:
`audit.generate` → six × `audit.worker` (a chord) → `audit.finish`.

**An agent turn.** One chat message can cost several model calls and several writes. Task
name: `agent.run_turn`.

Both own a **database row** — `audit_jobs` / `agent_turns` — with status, stage and error, so
a finished job stays findable after the broker has forgotten the task. Progress is read from
the row, not from Celery.

There are **no custom queues**: everything runs on Celery's default queue.

With no worker running, jobs stay `pending` and the UI honestly shows "Audit queued". For
tests and any caller without a broker, `run_job(job_id, session_factory)` chains the three
steps in-process.

## Timeouts

| Setting | Default | Bounds what |
| --- | --- | --- |
| `AUDIT_JOB_TIMEOUT_SECONDS` | 900 | Celery-wide `task_time_limit`; soft limit is this minus 30 |
| `AGENT_TURN_TIMEOUT_SECONDS` | 180 | Set **per task**, because someone waiting at a keyboard is not an audit. Soft limit `max(t-15, 15)` |
| `SUGGESTIONS_TIMEOUT_SECONDS` | 60 | One LLM call in the suggestion layer |

## Where the AI sits

Two independent systems, different jobs, same model:

| | Suggestion layer | Agent |
| --- | --- | --- |
| Runs | Inside each audit worker | In its own Celery turn |
| Job | Draft text for a finding | Hold a conversation and act |
| Tools | none — one prompt, one JSON schema | eleven, calling the product's own functions |
| Providers | `vertex` or `gemini` | **vertex only** (tool-calling needs a chat binding) |
| If it fails | Recorded as `skipped` / `failed`; the audit is unaffected | The turn fails with the reason |

→ [ai-setup.md](ai-setup.md)

## Testing

```bash
cd backend && uv run pytest        # 364 tests
cd backend && uv run ruff check .  # line length 100
```

`asyncio_mode = "auto"`, so async tests need no decorator. The `session_factory` fixture
builds a fresh SQLite database per test. Three autouse fixtures make the suite hermetic:
provider stubs, an in-process fake Redis for the agent stream, and a `Settings` with no LLM
credentials — **no test can reach a language model or open a socket**, even by forgetting to
ask.

The frontend has no test suite; `npm run lint` and `npm run build` are the gate.

## Related

- [running-locally.md](running-locally.md) — get it up from nothing
- [configuration.md](configuration.md) — every environment variable
- [ai-setup.md](ai-setup.md) — configuring the AI, with a worked example
- [deployment.md](deployment.md) — the VM
