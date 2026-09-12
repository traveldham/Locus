# 009 — Background sync engine

**Status:** ❌ REMOVED — see [013-simplification.md](013-simplification.md)

> Built, then deleted. It paced requests against a Google quota that is zero, queued work
> that never had contention, and scheduled jobs through a Redis nobody had installed — for
> an owner managing one business. The `SyncRun` table survives as bookkeeping; the engine
> around it does not.
>
> Kept as a record of what was built and why it was wrong. The lesson is in 013: test the
> third-party blocker with one real call before designing infrastructure around it.

---

*Original notes below.*

## Goal

Keep the local copy of Google's data current, without the UI ever calling Google directly.

```
Google  →  sync worker  →  Postgres  →  API  →  UI
```

Screens read Postgres, so they are fast and cost no quota. Google allows roughly 300 requests per minute **per project, shared across all customers** — a handful of users refreshing dashboards would exhaust it if reads hit Google live.

## Redis is optional — deliberately

| Mode | When | Behaviour |
|---|---|---|
| Inline | `REDIS_URL` unset (the default) | The job runs in the API process. Everything works with nothing extra installed. |
| Queued | `REDIS_URL` set | Handed to an arq worker; the request returns immediately, and the nightly cron is enabled. |

`runner.enqueue()` is the single place that decides, so no caller branches on it. If Redis is *configured but unreachable* it logs a warning and runs inline rather than failing, bounded by a 3-second connect timeout with `conn_retries=1` — a dead Redis costs a moment, not a hung request.

This matters because the user has not installed Redis and must not be blocked on it.

## Run bookkeeping

Every attempt writes a `SyncRun`: kind, started, finished, records written, error.

Two details that took care:

- **`running` is committed immediately**, not at the end. A crashed process therefore leaves evidence, and the in-flight row is visible to the dedupe check.
- **On failure the session is rolled back before writing `failed`.** If the error poisoned the transaction, writing the failure into that same transaction would fail too — losing the error message at precisely the moment it is needed.

`run_job` never propagates an exception; it returns a `JobResult`. A broken sync cannot turn into a 500.

## Pacing

A **token bucket** (`SYNC_CALLS_PER_MINUTE`, default 60), not fixed spacing. A twelve-location account never waits; a five-hundred-location account is throttled. Applied before `list_accounts`, each `list_locations`, and each per-location refresh.

The HTTP client separately retries 429 and 5xx with exponential backoff **plus jitter**, so many concurrent jobs do not retry in lockstep.

## Deduplication

Requesting a sync of a kind already `running` for that org returns the in-flight run instead of starting a second. Holding down Refresh cannot stack duplicate work against the quota.

## Extension point

`register_job(name, kind, handler)` plus `EXTRA_JOB_MODULES`. The runner, worker and API all read the registry, so adding reviews / performance / media sync needs no edit to any of them. An unregistered kind returns 422 listing the valid ones. Import failures in extra modules are logged, never fatal.

## Schedule

With Redis: a daily cron at **03:07** refreshes location profiles for every org with a connected Google account. The odd minute is intentional — round times are when every other cron on the machine fires.

## Endpoints

| Method | Path | Notes |
|---|---|---|
| POST | `/sync/run` | Body `{ kind }`. `queued: false` means it already ran inline, so the returned row is final. |
| GET | `/sync/runs` | Newest first; powers "last synced" and error surfacing |
| GET | `/sync/runs/{id}` | |

## Verification

15 tests: a job opens and closes its run; **a failing job still closes its run as `failed`** with the error recorded; the inline fallback works with no Redis; `POST /sync/run` returns a run; a second request while one is running returns the existing run; listing is org-scoped and newest-first; cross-organization access 404s.

**Not verified:** never run against Redis or a real worker process.
