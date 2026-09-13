# Location audit engine

An audit is about one business profile, the way a site audit is about one site. It is
one pipeline with six independent workers, one per category:

| Worker | Category key | Weight |
| --- | --- | --- |
| Profile completeness | `profile` | 20 |
| Reputation | `reputation` | 20 |
| Local visibility | `visibility` | 25 |
| Operations | `operations` | 15 |
| Performance | `performance` | 10 |
| Content | `content` | 10 |

Every audit runs every worker. Each worker owns its checks, thresholds and wording in
its own module under `categories/`, and none reads another's result. The workers are
built one at a time; an empty `CHECKS` means that category is reported as not evaluated
and left out of the score.

## Pipeline

```
POST /runs  →  audit_jobs row + six audit_workers rows  →  Celery
                    audit.generate: read the snapshot once, store it on the job
                    audit.worker × 6: run one category, write result on its worker row
                    audit.finish (chord): assemble, score, publish the run, delete the old one
```

`GET /jobs/{id}` returns the pipeline with every worker's own status and stage. The
job's progress is the share of workers finished; it says nothing about how complete
the profile is. The current audit stays served throughout, and is replaced only once
the new one is written. One audit per profile at a time: a second request joins the
running one.

`app/tasks/audit.py` keeps the three steps as plain async functions (`prepare_job`,
`run_category`, `finish_job`, and `run_job` which chains them in-process) so tests and
any in-process caller need no broker.

## Engine

`engine.run_worker(snapshot, as_of, config, category)` is a pure function for one
worker; `engine.assemble(...)` scores the six results. `snapshot.py` reads one
location's rows in a repeatable-read transaction and strips identity metadata;
`contracts.py` maps every column to a role. `policy.py` gathers weights and check
docs from the workers and holds the severity bands and penalties. `scoring.py` turns
verdicts into a category score and a weighted health score: a check that abstains
leaves the denominator, never counts as a pass, and an enumerating check is scored on
the share of subjects that failed.

## Building a worker

In `categories/<key>.py`:

1. Declare each check in `CHECKS` with its weight inside the category and the wording
   the UI shows: `label`, `checks`, `fix`, `unit`, `predicate`, `predicate_one`,
   `subject`, `subject_predicate`.
2. Add any threshold the check needs to `EngineConfig` in `types.py`.
3. In `evaluate(c)`, call `c.assess(rule, state, reason, issues, evaluated)` exactly
   once per check and `c.emit(...)` once per finding, with evidence rows attached.
4. Add mutation tests: changed values change findings, missing evidence abstains.
5. Bump `ENGINE_VERSION` for any semantic change.

```sh
uv run pytest tests/test_recommendations.py tests/test_recommendation_scoring.py -q
uv run ruff check app/services/recommendations app/api/recommendations.py app/tasks
```
