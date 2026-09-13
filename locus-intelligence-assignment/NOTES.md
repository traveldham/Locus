# How to read this audit

## Decision and design

“Better” means addressing directly observed customer-service gaps first, investigating
measured deterioration second, and confirming optional profile/content gaps last. The
output is an audit — a health score per location, every issue behind it, and the rows
each issue rests on. It is not a forecast of revenue or a claim about Google's algorithm.

The engine reads the current organization's database into a repeatable-read snapshot,
then runs ten deterministic checks per location. It has no clinic IDs, city-specific
exceptions, prewritten diagnoses, or learned assumptions about this CSV's values. Field
contracts describe measurements, times, join keys, context and excluded identity
metadata. Not every column deserves a scoring weight: customer names are excluded;
service labels, geography and text provide context; counts are not proof of quality.
Adding a new source requires a documented adapter, not arbitrary key/value pairs.

Every check returns triggered, clear, insufficient_data or suppressed, and each rule
reports how many subjects it examined and how many failed. Checks that enumerate —
rankings and search terms — emit one issue per affected keyword or term rather than a
single representative, because a manager investigating lost visibility needs the list.
Severity is graded from magnitude, not fixed per rule: how many essential fields are
missing, what share of recent reviews is unanswered, how far a decline runs past its
threshold, whether a keyword was off-pack three weeks or never found at all.

The health score is the weighted share of *evaluated* checks that passed, reduced by
each failing check's severity and by the share of subjects it examined that failed.
Category weights are policy: local visibility 25, profile and reputation 20 each,
operations 15, performance and content 10. Severity bands are policy: critical from 75,
warning from 45, notice below. Checks without enough evidence are excluded from the
denominator and reported as coverage — a location with thin data scores nothing, never
a flattering pass. Scoring an enumerating rule on the share that failed, not the raw
count, keeps a clinic that tracks many keywords from being punished for tracking them.
These are versioned operating policies, not calibrated probabilities.

## What I trust—and what I do not

I trust a stored absent website, explicit missing image flag, or unanswered review as a
reason to verify or follow up. I trust arithmetic over the cited rows. I do not trust
the score as evidence that raising it will raise bookings or revenue; it ranks work.
Confidence describes the evidence, not the success of the proposed intervention.

Daily comparisons pair observed dates in adjacent 28-day, weekday-aligned windows,
require 80% coverage and minimum impression volume, and never fill missing days with
zero. Actions per impression are event intensity, not conversion probability. Monthly
search terms are truncated; only the same observed term in both complete months is
compared. Rankings require four consecutive fresh checks; not-found is not rank zero,
and same-week competitors are context rather than causal explanation.

FALSE attributes are configured; missing values need confirmation, not automatic
enablement. Settled outcomes read a 90-day window while requests read 28: a clinic's
appointment book cannot produce a reportable settled denominator in four weeks, and the
shorter window silently hid the finding rather than abstaining visibly. Future
appointments and unsettled statuses stay out of outcome rates. “New” requests may
reflect stale CRM statuses. Old posts may reflect an incomplete export — the supplied
files contain 69 posts despite DATA.md's stated 93. Different datasets cover different
periods and cannot be joined into a reliable acquisition funnel. The analysis date
selects dated observations; mutable profiles, replies and booking statuses remain
current stored state, not reconstructed history.

## What the data says

Fleet health is 69/100 across all twelve clinics, from 60 (Irving) to 78 (Plano Legacy),
over 181 issues: 23 critical, 134 warning, 24 notice. The two weak categories are real
and independent of the scoring policy.

Local visibility averages 48. Only 6.7% of the 1,411 weekly rank observations put a
clinic in the local pack, and 101 of 112 tracked keywords were outside it in all four
recent checks. That is the fleet's headline problem, and it is a property of the data,
not of a threshold.

Operations averages 41. Of the six clinics with enough settled past visits to measure,
every one exceeds the 20% policy threshold for cancellations and no-shows, between 39%
and 56%. Eleven of twelve still carry appointment requests marked new past the wait
window. The remaining six clinics abstain: fewer than twenty settled visits in 90 days
is not a reason to report a rate.

Performance is almost entirely flat, and the one real fall is small: Irving lost 10.0% of
its impressions. A flat 20% trigger classed that as nothing to see. Reporting from a 10%
floor and grading severity from the size of the fall surfaces it as a notice — visible,
ranked below a critical operations gap, and neither suppressed nor inflated.

## Scope and next week

The supplied output uses the documented snapshot date, 2026-09-11. JSON carries the
scores, metrics, issues and coverage; evidence.json carries the cited source rows;
Markdown is the human-readable audit. Tests cover changed inputs, deterministic replay,
missing data, tenant isolation, archived evidence, recalculated evidence totals, and the
scoring rules themselves — that abstention never earns credit, that a wide failure
scores worse than a narrow one, and that tracking more keywords does not lower a score.

No LLM, embeddings, predicted uplift, automatic public writes, continuous
synchronization, or universal arbitrary-schema reasoning is claimed. LLM use is optional
in the brief; a complete deterministic explanation is more defensible than unvalidated
interpretation. Another week would add human-reviewed review-theme extraction with cited
text, ingestion watermarks, incremental recomputation, operator feedback and outcome
tracking, and score weights that a customer can adjust and see explained. Only then
would I evaluate learned ranking against observed outcomes, and test whether an LLM
actually improves usefulness.
