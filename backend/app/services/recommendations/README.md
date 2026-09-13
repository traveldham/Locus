# Changing-data location audit engine

`engine.analyze(snapshot, as_of, EngineConfig(...))` is a pure analysis function. Names
and IDs identify evidence; they never select special business-specific rules. Same
snapshot, date, policy and engine version reproduce the same findings. Run comparison
is a separate operation against the previous saved run.

## Data → decisions → evidence

`contracts.py` maps all analytical tables and every model column to a role. Reviews
include replies; categories/hours are normalized children. `snapshot.py` reads one
location's rows in a PostgreSQL repeatable-read transaction and removes
identity/ingestion metadata. The attribute catalog stays organization-wide because it is
a shared vocabulary; competitors are reached through that location's tracked keywords. `profile.py`, `operations.py`, `performance.py` and
`rankings.py` interpret documented fields. `runs.py` saves the full input snapshot,
report, version, configuration and fingerprint, then deletes the audit it replaced: one
current audit per business profile, no history to browse or store. APIs never mutate it.

An audit is about a single profile, the way a site audit is about a single site. Each
location has its own run, its own job and its own last-audited time, and they are audited
independently — one profile's rerun leaves the other eleven untouched.

Generation is queued, not run inside the request. `POST /runs` creates an `audit_jobs`
row, hands it to Celery and returns 202 with the job; `app/tasks/audit.py` runs it on a
worker, committing a stage and percentage as it reads, checks, compares and saves, and
recording the run id or the error on the job. One audit per profile at a time: a
second request for the same profile joins the running job rather than racing it. The
current audit stays served throughout, so the dashboard never goes blank, and is only
replaced once the new one is written. `GET /latest` carries any active job alongside the
run; `GET /jobs/{id}` is what the UI polls.

`compare()` still runs against the audit being replaced, so "new since the last audit"
and each location's score change ride on the report itself rather than requiring the
earlier audit to be kept.

All ten rules return triggered, clear, insufficient_data or suppressed, and report how
many subjects they examined against how many failed. `policy.py` holds the audit policy —
category weights, severity bands and penalties — and `scoring.py` turns verdicts into a
health score per location plus a fleet rollup and issue clustering. `metrics.py` adds the
observed measurements shown beside the score; an unavailable metric says so rather than
reporting zero. Rankings and search enumerate every affected keyword or term, each with
its own `subject` so a finding keeps its identity across runs.

A check that abstains is excluded from the score's denominator, never counted as a pass,
and an enumerating rule is scored on the share of subjects that failed so that tracking
more keywords cannot by itself lower a score. See the assignment's
[NOTES](../../../../locus-intelligence-assignment/NOTES.md) for thresholds and deliberate
limits. `/api/v1/recommendations/contracts` exposes the typed field inventory and
semantics; `/api/v1/recommendations/policy` exposes the scoring policy so the UI never
hardcodes it. New schemas need explicit adapters.

## Run against existing data

From `backend/`, after applying migrations:

```sh
uv run alembic upgrade head
uv run python -m app.services.recommendations.export \
  --organization brightpath-dental-group --as-of 2026-09-11 \
  --output ../locus-intelligence-assignment/output
```

This adds a saved run and writes three output files: the full audit JSON, the cited
evidence rows, and a human-readable Markdown audit report. It does **not** seed/import or
change business records. Do not reseed merely to refresh recommendations: seeding
refreshes fixture values and can overwrite edits. Use another output directory to
preserve an earlier export. Dates in the future are rejected. The app's default is
today (UTC), not the fixture's date; stale fixtures will correctly lose eligibility.

The audit is about one location at a time, the way a site audit is about one site.
`/recommendations` lists every location with its score, issues and coverage;
`/recommendations/<location>` is that location's audit in two sections. Overview: score
against the fleet median, checks run, area scores, severity counters with trend, top
issues and measurements. Issues: one line per check, written as a sentence -
"105 keywords are outside the local pack" - grouped by severity, filtered by area,
severity and search, all held in the URL. Removing the "With issues" filter reveals the
checks that passed or could not run, each with its reason. Opening a check's count gives
a detail page with a failed/passed bar, how to fix it, and a searchable table of the
affected keywords, terms or locations with the evidence underneath. 

`RULE_DOCS` in `policy.py` holds the per-rule explainer the UI shows — what the check
looks at and what to do about it — written once per rule and phrased as verification
steps, never as an asserted ranking or revenue outcome.
It checks current inputs every minute while mounted; it does not generate automatically.
The POST `/api/v1/recommendations/runs` accepts `as_of` and optional validated `config`.
GET `/latest`, `/runs`, `/runs/{id}` and `/runs/{id}/evidence` are organization-scoped.

## Extend and verify

Add a focused evaluator using `Context`; attach exact source IDs and calculations,
guard unknown values and date coverage, call `assess` exactly once per rule with the
subjects examined, then register it in `engine.py` and give it a category in `policy.py`.
Add mutation tests proving changed values change findings and missing evidence causes
abstention.
Increment ENGINE_VERSION for semantic/rule changes. Configuration changes are explicit
policy changes, not measured business improvements. There is no LLM in this version.

```sh
uv run pytest tests/test_recommendations.py tests/test_recommendation_scoring.py \
  tests/test_recommendation_output.py -q
uv run ruff check app/services/recommendations app/api/recommendations.py
```

Prototype limits: the snapshot stored with each profile's audit costs roughly 115 KB, and scans are not optimized for a large fleet. Current snapshots do not prove external feed completeness.
Free text may contain identifying details even though explicit customer identity
columns are excluded; production retention/privacy controls are required before
using real customer data. The bundled evidence is synthetic.
