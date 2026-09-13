# 019 — Changing-data location audit engine

Status: COMPLETE. Authorized 2026-09-13.

Build a reusable engine over the current organization's database: versioned field contracts,
immutable evidence snapshots, configurable rules, explicit abstentions, graded severity,
health scoring, run comparison and an audit UI. No hardcoded business IDs or invented uplift.
Generation is explicitly requested; saved runs are checked against current inputs for staleness.
Optional LLM interpretation is deferred; the shipped deterministic explanations are complete.

Done: ten rules with magnitude-graded severity; rankings and search enumerate every affected
keyword and term; a 90-day settled-outcome window separate from the 28-day request window;
tiered performance reporting from a 10% floor; per-location health scores and category
subscores where abstaining checks leave the denominator rather than scoring as passes;
per-location metrics; fleet rollup and issue clustering; `/policy` endpoint; Markdown audit
report; 24 engine/API/output tests. Real output regenerated for all twelve locations.

UI: the audit is single-location, structured after Semrush Site Audit and Ahrefs Site Audit
and mapped to Google Business Profile. `/recommendations` is a location directory;
`/recommendations/<location>` is one location's audit with Overview, Issues, Progress and
Compare. Issues are one-line sentences grouped by severity with area/severity/search filters
in the URL, a removable "With issues" filter that reveals passed and unevaluated checks with
their reasons, and a per-check detail page carrying a failed/passed bar and the affected
subjects with evidence. Generation runs on Celery over Redis with an `audit_jobs` row carrying live stage and
percentage; the dashboard shows that status while continuing to serve the current audit.
There is no audit history: a run replaces the one before it, and the comparison against
the replaced audit is carried on the report so "new since last audit" still works.
An audit is scoped to one business profile: each location has its own run, job and
last-audited time, and rerunning one leaves the others untouched. The organization
benchmark is computed across the current audits at read time. The dashboard is
project-scoped: `?project=` drives an ActiveProjectProvider, the header switcher rescopes
the current page instead of navigating away, and profiles are audited automatically
when a project is created or locations are added to one - always freshly, so a project
never opens onto someone else's older result. The audit stays keyed to the profile, not
the project: profiles shared across projects share one current audit.

Next: PDF and CSV export, per-tenant check exclusion, pushing an issue to a task tracker,
and a cheap input watermark to replace the full-snapshot hash on `/latest`.

Historical analysis dates select observation windows; mutable profile/booking/reply fields remain
current state, not a reconstruction of past state. Never reseed to generate recommendations.
