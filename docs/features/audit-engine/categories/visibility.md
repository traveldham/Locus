# Local visibility worker

Category `visibility`, weight 25. Module: `backend/app/services/recommendations/categories/visibility.py`.
Suggestion layer: `backend/app/services/recommendations/suggestions/visibility.py`.
Research and thresholds: `docs/features/audit-engine/research/05-visibility-worker.md`.

## What it answers

Does the profile show up when people search, and against whom? Five groups of checks.
Every check is deterministic. A permanently closed profile suppresses every check. A
stale rank tracker abstains every rank check; the search-term checks still run.

| Group | Rule | Weight | Severity | Fails when | Abstains when |
| --- | --- | --- | --- | --- | --- |
| Tracking | `tracking_stale` | 2 | warning | latest weekly rank check older than `rank_freshness_days` (21) | no keywords or no rank checks |
| Local pack | `pack_share_low` | 3 | warning | share of keywords in the pack in the latest week below `pack_share_min` (0.25) | tracker stale; no keyword checked in the latest week |
| Local pack | `pack_lost` | 2 | warning | keyword in the pack in an earlier week of the `rank_trend_weeks` (4) window and not in the latest, one finding per keyword | same |
| Local pack | `near_pack_opportunity` | 2 | notice (opportunity) | keyword at positions `near_pack_low`..`near_pack_high` (4..8) in `near_pack_min_weeks` (2) or more of the window and not in the pack now, one per keyword | tracker stale; no keywords |
| Keywords | `not_found_persistent` | 3 | warning | not found in `not_found_min_weeks` (4) consecutive weeks ending in the latest, one per keyword | no keyword has that many consecutive checks |
| Keywords | `rank_dropped` | 2 | warning | latest position worse than the mean of the earlier window weeks by `rank_drop_min_positions` (3), one per keyword | no keyword has a position in two weeks |
| Keywords | `high_intent_lagging` | 2 | warning | a keyword whose intent is in `high_intent_intents` sits `high_intent_lag_positions` (3) behind the median of the other keywords, or is not found, one per keyword | no high-intent keyword, or no other keyword with a position |
| Keywords | `branded_not_first` | 3 | warning, critical if not found | a keyword carrying a brand word is not at position 1 | no branded keyword tracked (true of the sample data) |
| Search demand | `search_term_losing` | 2 | warning | exact-month pair (latest complete month and the one before), earlier month at or above `term_loss_min_impressions` (200), loss at or above `term_loss_share` (0.5), one per term | no terms reaching the month before the latest complete month; no pair above the floor |
| Search demand | `service_not_surfacing` | 1 | notice | a project service none of the latest month's terms mention, one per service | no projects or no terms |
| Rivals | `rival_ahead_gap` | 2 | notice to warning | a rival ahead on `rival_min_keywords_ahead` (3) or more keywords in the latest week with `rival_review_ratio` (1.5x) reviews, `rival_rating_gap` (+0.3) rating or `rival_photo_ratio` (1.5x) photos, one per rival | no observations for the latest week, or nothing of our own to compare |

Semantics that matter:

- A keyword not found has no position. Nothing averages over it.
- Weeks are slots built from the latest check; a missing slot is unchecked, not unfound.
- Rivals are compared only inside the same keyword and week, and only when our profile
  was checked on that keyword that week. Our side comes from the `reviews` and `media`
  rows in the snapshot.
- Brand words are the words of the stored name minus the trade words and the city.
- Threshold search-term rows (Google's "fewer than N") are never paired.
- The month of the analysis date is incomplete and never compared.

## Card

`card(snapshot)` returns: `latest_week`, `weeks` (the four slots), `keywords_tracked`,
`in_pack`, `near_pack`, `not_found`, `pack_share`, `best` and `worst` found keyword with
position, `keywords` (keyword, intent, device, latest position, in_pack, four-week
trend, weeks in pack), `top_terms` (top five of the latest month with change against the
month before, threshold flag), `terms_month`, `rivals_ahead` (top five by keywords
ahead with their reviews, rating, photos) and `ours`.

Frontend: `frontend/src/components/recommendations/cards/visibility-card.tsx` exports
`VisibilityCard` (typed to `CategoryCardProps`, with its own `VisibilityCardData`
interface): pack-share ring, three counters, the keyword table with a sparkline and
status tags, the draft plan next to a keyword that has one, top search terms with change
and any term action, and rivals ahead against our own figures. It is registered in
`cards/registry.ts` by whoever owns that file.

## Suggestions

| Check | Field drafted | Shape |
| --- | --- | --- |
| `near_pack_opportunity`, `high_intent_lagging` | `keyword_plan` | map of the finding's keyword to one sentence naming the profile change |
| `search_term_losing` | `term_action` | one sentence naming the profile change that answers the term |

The prompt carries the profile basics (name, categories, city, description), the keyword
table (keyword, intent, device, latest position, weeks in the pack), the top search
terms, the rivals ahead, our own figures and every project the location belongs to.
Enforced in code, not by the prompt: a plan is kept only for the keyword the finding
names; values with a URL, an email or a phone number are dropped; sentences are capped
at 240 characters. `fallback_summary` is deterministic and names the branded problem,
the pack share, the near-pack keywords, losing terms and rivals ahead.

## Tests

- `backend/tests/test_visibility_worker.py`: every check declared and assessed once, a
  healthy tracker scores 100, and one mutation per check flips its verdict or abstains,
  including the stale tracker, consecutive-week semantics, exact-month pairing,
  threshold rows, the brand-word heuristic and the rival same-week rule.
- `backend/tests/test_visibility_suggestions.py`: target selection, context and prompt
  content, attachment of validated drafts, dropped links and phones, sentence cap,
  deterministic summary.

## Not built yet

Keyword search volume, the tracker's grid or radius, rival categories and services, and
Google's own per-keyword impressions: none are in the export, and each would let the
worker weight opportunities by demand or name a relevance gap instead of a prominence one.
