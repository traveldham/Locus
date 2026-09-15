# Audit engine

**What it is.** Point it at one Google Business Profile and it returns a health score, every
issue behind that score, and the stored rows each issue rests on. It is an audit, not a
forecast: it ranks work, it does not predict revenue.

Engine version **4.0.0**. Code under `backend/app/services/recommendations/`.

## The one idea

One Google Business Profile is one location. One audit is about one location. An audit is a
single pipeline holding **six independent workers**, one per category. Every audit runs
every worker. A worker never reads another worker's result.

```
POST /recommendations/runs
        │
   prepare ──── read the profile's rows once into a repeatable-read snapshot
        │
   6 workers ── each runs its own category's checks over that snapshot
        │
   finish ───── assemble → score → publish the run, delete the previous one
```

## What it produces

| | |
| --- | --- |
| **Health score** | 0-100, or `null` when nothing could be evaluated |
| **Grade** | excellent / good / fair / poor / not_evaluated |
| **Coverage** | share of checks that could actually be judged |
| **Category scores** | six of them, each `null`-able |
| **Findings** | one per issue, with title, why, action, severity, confidence, limitation |
| **Evidence** | per finding: source table, row ids, fields, the calculation, the values |
| **Check inventory** | every check the engine can run and what it concluded |
| **Priorities** | the few findings to do first |
| **Cards** | per-category display data: the review spread, the keyword table, the funnel |
| **Suggestions** | AI drafts for the findings that declare a draftable field |

Every finding is traceable. A recommendation a location manager cannot follow back to a
row in the database is not finished.

## The six categories

| Order | Worker | Key | Weight | Scope |
| --- | --- | --- | --- | --- |
| 1 | Profile completeness | `profile` | 20 | Name, categories, phone, website, description, address, hours, attributes, verification |
| 2 | Reputation | `reputation` | 20 | Rating, volume, velocity, reply rate, reply speed, unanswered complaints |
| 3 | Local visibility | `visibility` | 25 | Search terms, local pack, tracked keyword positions, rivals |
| 4 | Operations | `operations` | 15 | Appointment requests, response, cancellations, no-shows |
| 5 | Performance | `performance` | 10 | Impressions, calls, directions, website clicks, trends |
| 6 | Content | `content` | 10 | Photos, videos, posts, freshness |

Weights sum to 100 and are asserted at import time. Each worker's checks, thresholds,
abstentions and AI drafts are documented in [categories/](categories/).

## The rule that governs everything

**Checks without enough evidence are excluded from the score, never scored as passes.**

A profile with thin data therefore reports low coverage and a `not_evaluated` grade — it
does not report a bad score. If you are wondering why a clearly neglected profile scored
well, look at coverage before you look at the thresholds. See [scoring.md](scoring.md).

## Where things live

| Path | What |
| --- | --- |
| `categories/<key>.py` | One worker: its `CHECKS` declaration and its `evaluate(c)` |
| `types.py` | `EngineConfig` — every threshold, `extra="forbid"` |
| `policy.py` | Category weights, severity bands, penalties, grades |
| `scoring.py` | Verdicts → category scores → health score |
| `engine.py` | `run_worker`, `assemble`, `analyze` — pure functions |
| `context.py` | What a worker is handed: snapshot, location, date, config, `assess`/`emit` |
| `snapshot.py` | Reading one profile's rows into the analysis input |
| `contracts.py` | Which tables feed the engine, and every field's role |
| `suggestions/` | The AI draft layer, one module per category |
| `queue.py`, `runs.py` | Starting audits, storing and serving the current run |
| `backend/app/tasks/audit.py` | The three pipeline steps and their Celery wrappers |

## Thresholds

Every threshold is a field on `EngineConfig` with `extra="forbid"`, so a magic number
cannot hide inside a rule body. The config is stored on the job, so a run records the exact
policy it was scored under. Callers may override it per run.

A few that catch people out — the full list is in `types.py`:

| Knob | Default | Why it matters |
| --- | --- | --- |
| `min_reviews` | 5 | Below this, rating checks abstain rather than fire |
| `reply_wait_days` | 3 | A review younger than this is excluded from reply maths |
| `min_critical_reviews` | 3 | Below this, the complaint reply rate abstains |
| `booking_min_settled` | 10 | Below this, cancellation and no-show rates abstain |
| `performance_min_impressions` | 200 | Below this in either window, no trend is computed |
| `performance_min_paired_share` | 0.7 | Days must pair across both windows to be compared |
| `not_found_min_weeks` | 4 | Consecutive weekly checks needed to call a keyword lost |
| `content_posts_min_90d` | 6 | Roughly one post a fortnight |

## Running one

```
POST /api/v1/recommendations/runs   {"location_id": "<uuid>", "as_of": "2026-09-14"}
GET  /api/v1/recommendations/jobs/{id}         → progress, six worker rows
GET  /api/v1/recommendations/latest?location_id=…  → current run, active job, inputs_changed
GET  /api/v1/recommendations/policy            → weights, bands, every rule's documentation
GET  /api/v1/recommendations/contracts         → every input field and its role
```

One audit per profile at a time: a second request joins the running one. In-process, for
tests and any caller without a broker:

```python
from app.tasks.audit import run_job
await run_job(job_id, session_factory)
```

## Rules for building a worker

1. Decide the checks from subject-matter expertise first, write them down, then code.
2. One `assess` per check, always, including when it fires.
3. Never treat a missing row as zero. Abstain instead.
4. Wording is for a location manager: what was found, what to do. No column names.
5. Mutation tests: changed inputs change findings; missing evidence abstains.
6. Bump `ENGINE_VERSION` for any semantic change.

## Related

- [architecture.md](architecture.md) — pipeline mechanics, storage, the worker contract
- [scoring.md](scoring.md) — the scoring model in full
- [suggestions.md](suggestions.md) — the AI draft layer
- [categories/](categories/) — one document per worker
- [research/](research/) — the subject-matter research behind the checks
- [../demo-profiles/overview.md](../demo-profiles/overview.md) — deliberately bad profiles for exercising all of this
