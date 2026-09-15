# Running it

From nothing to a working app with data in it.

## What the app is, in one paragraph

Locus manages **Google Business Profiles** for a multi-location business. You sign in, see
every profile you run, open one, and audit it against 67 deterministic checks across six
categories — profile completeness, reputation, local visibility, operations, performance and
content. The audit returns a health score, every issue behind it, and the stored rows each
issue rests on. For the issues it can, it drafts the fix: a reply to an unanswered review, a
rewritten description, two Google posts, a photo shot list. A floating AI agent sits on every
page and can do the work — reply, edit the profile, run a fresh audit — through the same code
paths the screens use.

The seeded demo business is **Brightpath Dental Group**: twelve clinics across Texas and
Arizona, with a year of reviews, a quarter of performance, ranking, booking and profile data —
about 8,900 rows. Ten more deliberately poor-quality businesses across other industries can be
imported with one click.

## Prerequisites

| | |
| --- | --- |
| Python ≥3.12 and [uv](https://docs.astral.sh/uv/) | backend |
| Node 20+ and npm | frontend |
| PostgreSQL 14+ | `createdb locus` |
| Redis | only for background work — see the shortcut below |
| Google Cloud project + `gcloud` | only for AI drafts and the agent |

## 1. Backend

```bash
cd backend
cp .env.example .env          # then edit SECRET_KEY at least
uv sync
createdb locus                # if it does not exist
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

On first boot the app **seeds itself** — the demo user, organization, Google connection,
twelve locations, 1,514 reviews with 874 replies, and the eight analytics tables. It is
idempotent and skipped on every later start.

To seed by hand, or to refresh it:

```bash
uv run python -m app.seed
```

It prints what it wrote and ends with the credentials.

```
API      http://localhost:8000
Docs     http://localhost:8000/docs
Health   http://localhost:8000/api/v1/health
```

## 2. Frontend

```bash
cd frontend
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > .env.local
npm install
npm run dev
```

```
UI    http://localhost:3000
Sign in    pawanpatrapp@gmail.com  /  Pawan 2000
```

The credentials are printed on the sign-in page and prefilled into the form.

## 3. The Celery worker

Audits and agent turns run off the request thread. Without a worker they stay queued and the
UI says so honestly.

```bash
cd backend
./start.sh                 # background, pid in .celery/worker.pid, log in .celery/worker.log
./start.sh --foreground    # or in this terminal
./stop.sh                  # warm shutdown, SIGKILL after 30s
```

`start.sh` checks Redis first and tells you what to do if it cannot reach it.

**No Redis?** Run tasks inline instead:

```bash
CELERY_ALWAYS_EAGER=true uv run uvicorn app.main:app --reload
```

Everything works; an audit just blocks the request that started it.

## 4. AI (optional)

Without it, the audit still runs and every finding is still produced — only the drafted text
is missing, recorded as `suggestions.status = "skipped"`. The agent will refuse with the exact
setting to fix.

```bash
gcloud auth application-default login
```

```
LLM_PROVIDER=vertex
VERTEX_PROJECT=your-gcp-project
VERTEX_LOCATION=global
VERTEX_MODEL=gemini-3.8-flash
```

→ [ai-setup.md](ai-setup.md) for the alternative API-key provider and a worked example.

## A five-minute tour

1. **Sign in** → you land on **Profiles**, twelve Brightpath clinics.
2. Open one → the Google-style preview, then **Manage profile data** to see hours,
   categories, attributes and the change history.
3. **Profile audit** in the sidebar → the directory of profiles with their scores. Open one
   and press **Run audit**. Six workers report; the score, the category rings and the issue
   list appear.
4. Open an issue → the **evidence** panel names the table, the row ids, the calculation and
   the values. Where the audit drafted a fix, the **suggestion** panel offers it — and
   publishes it through the real endpoint.
5. **Profiles → Import sample profiles** → tick a few of the ten deliberately bad businesses,
   import, and audit one. Scores land 46-70 with 68-104 findings, against the flagship
   clinic's 81.
6. Open the **agent** (bottom right) and ask *"how is this location doing?"*, then
   *"reply to the reviews nobody has answered"*.

## Tests

```bash
cd backend && uv run pytest        # 364 tests
cd backend && uv run ruff check .
cd frontend && npm run lint && npm run build
```

No test reaches a language model, a broker or the network.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| "The sample dataset is incomplete: … is missing." | The CSV directory moved. Set `SAMPLE_DATA_DIR` |
| Audit stuck on "Audit queued" | No Celery worker. Start one, or use `CELERY_ALWAYS_EAGER=true` |
| "Cannot reach Redis at …" | Start Redis, or use eager mode |
| Agent says a setting is missing | It names the setting. Usually `VERTEX_PROJECT` or expired ADC |
| Every suggestion says "skipped" | `SUGGESTIONS_ENABLED=false`, or no credentials configured |
| 401 loop in the browser | `NEXT_PUBLIC_API_URL` is missing the `/api/v1` suffix |
| CORS error | `FRONTEND_URL` must match the browser's origin exactly |
