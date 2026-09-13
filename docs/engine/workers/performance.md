# Performance worker

Category `performance`, weight 10. Module: `backend/app/services/recommendations/categories/performance.py`.
Suggestion layer: `backend/app/services/recommendations/suggestions/performance.py`.
Research and thresholds: `docs/engine/research/07-performance-worker.md`.

## What it answers

Are impressions and customer actions holding up against the four weeks before? Three
groups of checks. Every check is deterministic. A permanently closed profile suppresses
every check; stale data abstains every check.

| Group | Rule | Weight | Severity | Fails when | Abstains when |
| --- | --- | --- | --- | --- | --- |
| Trend | `impressions_decline` | 3 | notice to critical, graded 10% to 40% | weekday-paired impressions fell at least `performance_impressions_decline` (10%) | under `performance_min_paired_share` (70%) of days paired, or under `performance_min_impressions` (200) in either window |
| Trend | `calls_decline` | 2 | notice to critical, graded 15% to 50% | paired call clicks fell at least `performance_actions_decline` (15%) | days not paired, or under `performance_min_actions` (30) calls in the previous window |
| Trend | `directions_decline` | 2 | same | same, direction requests | same |
| Trend | `website_clicks_decline` | 2 | same | same, website clicks | same |
| Trend | `action_rate_decline` | 2 | notice to warning, graded 15% to 50% | (calls + directions + website clicks) / impressions fell at least `performance_action_rate_decline` (15%) relative | either volume floor |
| Mix | `surface_split_shift` | 1 | notice | Maps share of impressions moved at least `performance_split_shift_points` (0.10) either way | volume floor |
| Mix | `mobile_share_shift` | 1 | notice | mobile share of impressions moved at least `performance_split_shift_points` | volume floor |
| Coverage | `zero_action_days` | 2 | warning, graded up by streak length | at least `performance_zero_action_streak_days` (3) consecutive days with at least `performance_zero_action_min_impressions` (20) impressions and every action reported as 0 | fewer evaluable days than the streak length |
| Coverage | `data_gaps` | 1 | notice | at least `performance_data_gap_days` (3) calendar days in the current window have no row | never (once data exists) |

Semantics that matter:

- Windows are `performance_window_days` (28, a multiple of 7) long and end on the
  last day with data on or before the audit date, never on the audit date itself. The
  previous window ends 28 days earlier. Each current day is paired with the same
  weekday one window before; only days both windows report are compared.
- A missing day is unknown, not zero: it and its pair are dropped. A NULL metric is
  unknown, not zero: each metric pairs on its own.
- Newest data more than `performance_max_stale_days` (14) before the audit date
  abstains every check with the age in the reason. The sample export ends 2026-09-11;
  an audit run on 2026-09-14 still evaluates, one run in October does not.
- Actions are events, not customers. The action rate is engagement, not conversion,
  and every finding says so in its limitation.
- A zero-action streak requires impressions on each day, so "no data" never reads as
  "nobody acted". A NULL action breaks the streak.
- Every threshold is a field on `EngineConfig` with a `performance_` prefix and is an
  operating policy, not a Google rule.

## Card

`card(snapshot)` returns, for the same 28-day window: totals with previous-window
value, relative change and days reported for impressions (total, Maps, Search), calls,
directions, website clicks, conversations, bookings and the action rate; Maps share and
mobile share of current impressions; twelve weekly impression totals ending on the last
data day, each with its day count; days with data; and the window dates. Totals sum
only reported values and carry the count of days that reported.

Frontend: `frontend/src/components/recommendations/cards/performance-card.tsx` exports
`PerformanceCard` (typed to `CategoryCardProps`): five KPI tiles coloured by direction
and outlined when a check fired against them, a weekly impressions sparkline, Maps
versus Search and mobile versus desktop bars, a coverage note, and each finding's
drafted investigation plan. Registering it in `cards/registry.ts` is a separate step.

## Suggestions

After the checks run, the worker task calls the suggestion layer. It asks the configured
model for one draft per finding whose check declares `suggests`:

| Check | Field drafted | Shape |
| --- | --- | --- |
| `impressions_decline`, `calls_decline`, `directions_decline`, `website_clicks_decline`, `action_rate_decline`, `surface_split_shift`, `zero_action_days` | `investigation_plan` | list of 3 to 5 checks, each under 160 characters, ordered by likelihood, no links, phone numbers or promises |

The prompt carries the stored profile (name, categories, city, open status,
verification, pending edits, phone presence, website, hours days), every project the
location belongs to, the window dates, and every metric's current, previous and change.
The model is told a plan is a checklist, never a diagnosis, and never to promise calls,
customers, rankings or revenue. Code enforces the list length, item length, and the ban
on URLs, e-mail addresses, phone numbers and promise words; a summary that breaks the
ban is discarded in favour of the deterministic one.

Each finding then carries `suggestion` with `field`, `value` (the list), `reason`,
`confidence`, `source`, `model` and `generated_at`. Verdicts and scores are never
affected by the suggestion pass. `fallback_summary` orders the findings by severity and
ends with "These are measured changes, not causes; check before acting."

## Tests

- `backend/tests/test_performance_worker.py`: every check declared and assessed once, a
  steady profile scores 100, permanent closure suppresses, no rows and stale data
  abstain, windows anchor on the last data day, graded declines, one check per action,
  action rate, weekday pairing, missing days dropped from both windows, NULL as unknown,
  thin volume abstains, share shifts, zero-action streaks, and the card.
- `backend/tests/test_performance_suggestions.py`: target selection, context and prompt
  content, attachment and validation of plans, banned content dropped, deterministic
  fallback, steady profile skips the model.

## Not built yet

Fleet or area comparison to separate seasonal demand from a local problem; a profile
edit log to line a drop up with an edit date; `BUSINESS_CONVERSATIONS` and
`BUSINESS_BOOKINGS` trends (reported on the card, not checked, because the sample has
no partner bookings context); website uptime.
