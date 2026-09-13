# Audit engine architecture

Status: all six workers built, 2026-09-14. Engine version 4.0.0.

## The one idea

One Google Business Profile is one location. One audit is about one location. An
audit is a single pipeline that holds six independent workers, one per category.
Every audit runs every worker. A worker never reads another worker's result.

```
                        ┌──────────────────────────────────────────────┐
  POST /runs   ──────▶  │  audit_jobs (the pipeline)                   │
                        │   status · as_of · config · snapshot         │
                        │                                              │
                        │   audit_workers ×6 (one per category)        │
                        │    profile · reputation · visibility         │
                        │    operations · performance · content        │
                        │    each: status · stage · result · error     │
                        └──────────────────────────────────────────────┘
                                          │
     prepare ─── read the profile's rows once, store as snapshot on the job
        │
     worker ×6 ─ run one category's checks over the snapshot, write result
        │
     finish ──── all six reported? assemble → score → publish run, delete old run
```

## Categories and weights

| Order | Worker | Key | Weight | Scope of the checks |
| --- | --- | --- | --- | --- |
| 1 | Profile completeness | `profile` | 20 | Business info: name, categories, phone, website, description, address, hours, attributes, verification |
| 2 | Reputation | `reputation` | 20 | Reviews: rating, count, velocity, reply rate, reply speed, unanswered critical reviews |
| 3 | Local visibility | `visibility` | 25 | Search terms, local-pack presence, tracked keyword positions, competitors |
| 4 | Operations | `operations` | 15 | Appointment requests, response, cancellations and no-shows |
| 5 | Performance | `performance` | 10 | Impressions, calls, directions, website clicks, trends |
| 6 | Content | `content` | 10 | Photos, videos, posts, freshness |

Weights sum to 100 and are asserted at import time. They are policy, not measured fact.

## What a worker is

`backend/app/services/recommendations/categories/<key>.py`, one module each:

```python
KEY = "profile"
LABEL = "Profile completeness"
WEIGHT = 20

CHECKS: dict[str, dict] = {
    # "rule_key": {"weight": 3, "label": ..., "checks": ..., "fix": ...,
    #              "unit": ..., "predicate": ..., "predicate_one": ...,
    #              "subject": ..., "subject_predicate": ...},
}

def evaluate(c: Context) -> None:
    # one c.assess(...) per rule, one c.emit(...) per finding
```

- `CHECKS` declares every check the worker owns, its weight inside the category, and
  the wording the UI shows. Policy reads this; nothing about a check lives elsewhere.
- Thresholds a check needs go on `EngineConfig` in `types.py`. Unknown knobs are
  rejected, so a threshold cannot hide in a rule body.
- `evaluate` gets a `Context`: the snapshot, the one location, the analysis date, the
  config, and `rows(source)`, `window(...)`, `assess(...)`, `evidence(...)`, `emit(...)`.

## Verdicts, findings, score

Each check ends in exactly one verdict:

| State | Meaning | Effect on score |
| --- | --- | --- |
| `triggered` | The check found an issue | Loses credit by severity and by share of subjects failed |
| `clear` | The check passed | Full credit |
| `insufficient_data` | Not enough evidence to judge | Left out of the denominator |
| `suppressed` | Does not apply (e.g. permanently closed) | Left out of the denominator |

A finding (`Recommendation`) carries title, why, action, score 0-100, severity
(critical ≥75, warning ≥45, notice), confidence, limitation, and evidence: source
table, row ids, fields, calculation, values. Enumerating checks emit one finding per
subject (keyword, term, field) with a stable key.

Category score = weighted share of that category's evaluated checks that passed,
minus penalties. Health score = weighted mean of the categories that were evaluated.
A category with no checks, or none that could run, is `null` and excluded. An empty
engine therefore scores `null`, never 100.

## Pipeline mechanics

- `POST /api/v1/recommendations/runs` creates one `audit_jobs` row with six
  `audit_workers` rows and hands the job id to Celery. One audit per profile at a time:
  a second request joins the running one.
- `audit.generate` runs `prepare_job`: repeatable-read snapshot of the profile's rows,
  stored on the job. Then a Celery chord fans out six `audit.worker` tasks and runs
  `audit.finish` once all six have returned.
- `audit.worker` runs `run_category`: never raises; success or failure is written on the
  worker row.
- `audit.finish` runs `finish_job`: if any worker is still pending or running, do
  nothing; if any failed, fail the job and name the categories; else assemble, score,
  save the run, delete the previous run, clear the snapshot from the job.
- `GET /jobs/{id}` returns the job with every worker. `progress` is the share of workers
  finished. `stage` reads "Reading stored records" or "N of 6 workers finished".
- `GET /latest?location_id=` returns the current run, any active job, and
  `inputs_changed` (snapshot fingerprint or engine version differs).
- Projects: creating a project or adding locations queues an audit for each profile.

The three steps are plain async functions in `backend/app/tasks/audit.py`, and
`run_job` chains them in-process for tests and any caller without a broker.

## Storage

| Table | Holds |
| --- | --- |
| `recommendation_runs` | One current audit per location: report JSON, snapshot JSON, fingerprint, engine version |
| `audit_jobs` | One pipeline per request: status, as_of, config, snapshot while running, run_id, error |
| `audit_workers` | Six per job: category, status, stage, result JSON, error, timings |

No audit history is kept. A new run replaces the old one.

## Inputs available to workers

The snapshot holds, for the one location: `locations`, `hours`, `categories`,
`attributes`, `catalog` (organization-wide vocabulary), `reviews` (with replies),
`performance` (daily), `search_terms` (monthly), `media`, `posts`, `bookings`,
`keywords`, `ranks` (weekly), `competitors` (via the location's keywords). Identity
and ingestion metadata are stripped. `GET /recommendations/contracts` lists every
field and its role.

## Rules for building a worker

1. Decide the checks from subject-matter expertise first, write them down, then code.
2. One `assess` per check, always, including when it fires.
3. Never treat a missing row as zero. Abstain instead.
4. Wording is for a location manager: what was found, what to do. No raw column names
   in user-facing text.
5. Mutation tests: changed inputs change findings; missing evidence abstains.
6. Bump `ENGINE_VERSION` for any semantic change.

## Worker docs

Each worker's checks, thresholds, abstentions and AI drafts are documented in
`docs/engine/workers/<key>.md`, with the research behind them in
`docs/engine/research/`.

## What was deliberately removed on 2026-09-13

Ten earlier rules, previous-vs-current comparison, metrics panel, organization
benchmark, fleet rollup, export CLI. They were retired so each category can be
rebuilt from scratch, one worker at a time, starting with profile.
