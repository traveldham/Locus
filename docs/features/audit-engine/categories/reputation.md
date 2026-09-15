# Reputation worker

Category `reputation`, weight 20. Module: `backend/app/services/recommendations/categories/reputation.py`.
Suggestion layer: `backend/app/services/recommendations/suggestions/reputation.py`.
Research and thresholds: `docs/features/audit-engine/research/04-reputation-worker.md`.

## What it answers

What do customers read about the business, and does the business answer? Five groups
of checks. Every check is deterministic. A permanently closed profile suppresses every
check. Reviews without a usable date are ignored; reviews without a star rating are
invalid for rating maths but still count as stored reviews.

| Group | Rule | Weight | Severity | Fails when | Abstains when |
| --- | --- | --- | --- | --- | --- |
| Rating | `rating_low` | 3 | warning, critical below `rating_critical_min` | mean rating over `rating_window_days` (90) below `rating_warning_min` (4.0); critical below `rating_critical_min` (3.5) | fewer than `min_reviews` (5) rated reviews in the window |
| Rating | `one_star_share_high` | 2 | warning | share of 1-star reviews over `review_lookback_days` (365) above `one_star_share_max` (0.10) | fewer than `min_reviews` rated reviews in the lookback |
| Trend | `rating_trend_falling` | 2 | warning | mean of the last window fell more than `rating_drop_max` (0.3) below the window before | either window has fewer than `min_reviews` |
| Volume | `reviews_few_vs_competitors` | 2 | notice to warning | stored review count below `competitor_review_ratio_min` (0.5) of the median competitor review count, latest week per keyword | no competitor row with a review count for the location's keywords |
| Recency | `no_recent_review` | 2 | notice to warning | newest review older than `review_gap_max_days` (30) | no reviews stored |
| Recency | `review_velocity_low` | 1 | notice | reviews in the last 30 days below `reviews_per_month_min` (3) | no reviews stored |
| Responsiveness | `reply_rate_low` | 3 | warning to critical | replied share of reviews older than `reply_wait_days` (3) in the lookback below `reply_rate_min` (0.6) | fewer than `min_reviews` eligible |
| Responsiveness | `critical_reply_rate_low` | 2 | warning to critical | replied share of 1 to 3 star reviews older than the wait below `critical_reply_rate_min` (0.8) | fewer than `min_critical_reviews` (3) eligible |
| Responsiveness | `critical_review_unanswered` | 3 | warning, critical for 1-star or long waits | any 1 to 3 star review older than the wait with a blank reply; one finding per review, newest first, at most `unanswered_list_max` (10) listed while the verdict counts all | no 1 to 3 star review older than the wait |
| Responsiveness | `reply_delay_high` | 2 | notice to warning | median days from review to reply above `reply_delay_max_days` (7) | fewer than `min_reviews` replies carrying both dates |

Semantics that matter:

- A blank or whitespace reply is no reply. Reply state is current, not historical: a
  reply added last week counts, and delay is measured from the reply's last update
  time, which moves if the reply is edited.
- Reviews younger than `reply_wait_days` are excluded from every reply-rate
  denominator, so a review posted yesterday never counts against the business.
- `star_rating` outside 1 to 5, null, or boolean is invalid and excluded from averages.
- No reviews is unknown, never zero velocity: recency and rating checks abstain. The
  competitor comparison still fires, because zero stored reviews against a known
  competitor median is exactly what it measures.
- The competitor benchmark uses each keyword's latest observed week, then the median
  across keywords, so one crowded keyword cannot dominate. It is marked medium
  confidence: stored rows and scraped counts are not measured the same way.
- Findings never carry a reviewer name. The subject of an unanswered-review finding is
  the Google review id, falling back to the row id.
- Every threshold is a field on `EngineConfig` in the reputation block and is an
  operating policy, not a Google rule.

## Card

`card(snapshot)` returns what a customer sees: `average`, `count`, `rated_count`,
`distribution` by star (5 to 1), `replied_share`, `median_reply_days`,
`last_review_date`, `unanswered_critical_count`, and `unanswered`: the latest five
unanswered 1 to 3 star reviews as id, rating, date and the first 140 characters of the
comment. The frontend card is `frontend/src/components/recommendations/cards/reputation-card.tsx`
(`ReputationCard`), which pairs each listed review with its drafted reply by subject.

## Suggestions

| Check | Field drafted | Shape |
| --- | --- | --- |
| `critical_review_unanswered` | `review_reply` | text under 350 characters, one per review: thank, acknowledge the specific concern, apologise where warranted, no private details, invite offline follow-up, no names, links, phones, emails or promotions |
| `rating_low`, `one_star_share_high`, `rating_trend_falling` | `themes` | list of up to eight short phrases naming recurring complaints and praise in the review text; confidence is capped at medium |

The prompt carries the business (name, category, city), every project the location
belongs to (name, website, description, services), the unanswered low reviews (id,
rating, date, comment up to 400 characters, reply present) and the forty most recent
reviews with text. Code enforces the reply length cap, rejects replies carrying a URL,
phone, email, greeting-plus-name, honorific or promotion, drops duplicates for one
finding, and deduplicates themes. `fallback_summary` is deterministic.

## Tests

- `backend/tests/test_reputation_worker.py`: every check declared and assessed once, a
  healthy review history scores 100, permanently closed suppresses, no reviews
  abstains, one mutation per check, null ratings and blank replies handled, list cap,
  card contents.
- `backend/tests/test_reputation_suggestions.py`: target selection, context without
  reviewer names, prompt content, attachment and validation of replies and themes,
  rejection of replies that break Google's guidance, failure recorded without losing
  findings, skip conditions. No real model is called.

## Not built yet

Review text sentiment as a deterministic check, reviewer-level patterns (the snapshot
deliberately drops identity), and reply quality scoring of existing replies. Rating
comparison with competitors' `average_rating` is left to the visibility worker.
