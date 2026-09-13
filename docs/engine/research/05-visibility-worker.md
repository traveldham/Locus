# 05 — Local visibility worker: research and check design

Research date: 2026-09-14. Scope: what "local visibility" means for one Google Business
Profile, what our own rank tracker and Google's search-term report can and cannot say,
and which checks discriminate between locations instead of failing all of them.

## 1. What the sources say

### The local pack is the prize

Google's own explanation of local ranking names three inputs: relevance, distance and
prominence, and says complete, accurate information makes a profile "more likely to show
up" (https://support.google.com/business/answer/7091; summarised in
`01-google-official-guidance.md`). The three-result "local pack" is what a searcher sees
first on Maps and on the results page; everything below it is a tap or scroll away.
Whitespark's 2026 Local Search Ranking Factors put Google Business Profile signals at
about a third of pack ranking, reviews at a fifth, with primary category, keywords in the
name, review recency and "open at time of search" as the top individual factors
(`02-industry-audit-factors.md`, section 1). BrightLocal's GBP audit benchmarks rank for
target keywords against the top ten (same document, "Local visibility" table).

### Positions 4 to 8 are the opportunity band

Rank position 1-3 is the pack. The industry rule of thumb for local rank trackers
(BrightLocal, Whitespark's Local Rank Tracker, Local Falcon) is that the next few
positions are the "fringe" where small profile changes move a listing into the pack,
while anything past page one is a relevance or distance problem, not a tuning one.
Sterling Sky's services-field test measured a 2-5% lift for service keywords within days
of adding services (`02-industry-audit-factors.md`, "Services field populated"): exactly
the kind of push that matters at position 5, and is invisible at position 40. So the
worker treats 4-8 as a positive finding to act on, not a failure.

### Branded versus non-branded

A search for the business's own name is a navigational query: the profile should be
first, and anything else signals a duplicate listing, a name mismatch, a suspension or a
verification problem. Non-branded terms ("emergency dentist plano") are the competitive
ones. The fixture keyword list carries no branded keyword at all (the brand surfaces only
in the search-term report, e.g. "brightpath dental"), so the branded check abstains on
sample data and is built for the production tracker.

### Volatility and single-week noise

Local rankings move by a few positions week to week on their own. In the fixture, the
week-over-week change of a found keyword is symmetric and mostly within ±3 (of 1,159
consecutive pairs: 202 unchanged, 161 up one, 154 down one, only 23 fell by five). A
single-week comparison therefore produces noise; the worker compares the latest week to
the mean of the previous weeks in the trend window, and the near-pack rule needs the
band to hold for two of four weeks.

### Search-term impressions

Google's search-term report lists queries that surfaced the profile, per month, and
withholds exact counts below a threshold (`is_threshold`). It truncates the long tail, so
term counts never sum to the daily impression total (DATA.md, "Known limits"). A term
that carried real volume last month and lost most of it is demand the profile is no
longer matched to. Terms must be paired on exact consecutive months; the current month
is incomplete and is never used.

### Competitor gap

Rival observations only exist in the context of a keyword and a week (three rivals per
keyword-week in the fixture, 4,233 rows). Comparing a rival's review count, rating or
photo count with ours is meaningful only for rivals that are ahead, and only when the
same rival is ahead on several keywords; a rival ahead on one term is noise. Reviews and
prominence signals are about a fifth of pack weight; photos matter for conversion and,
in visual industries, rank (`02-industry-audit-factors.md`, sections 1 and 4).

### The "not found" state

`rank_absolute` is empty when the tracker did not find the profile in the checked
results (DATA.md). That is not rank zero, not "worst possible", and must never be
averaged. The worker carries `None` and treats a keyword not found for several
consecutive weeks as its own finding.

## 2. What the fixture says (thresholds grounded in data)

Computed over `keyword_rank_weekly.csv`, `competitor_ranks_weekly.csv`,
`location_search_terms_monthly.csv`, `tracked_keywords.csv` on 2026-09-14.

| Fact | Value |
| --- | --- |
| Tracked keywords | 112 across 12 locations (8-12 each); 96 mobile, 16 desktop |
| Intents | general 33, cosmetic 22, emergency 17, orthodontics 15, implants 12, pediatric 12, insurance 1 |
| Weeks | 13, 2026-06-15 to 2026-09-07, every keyword checked in the latest week |
| Not found | 80 of 1,411 checks; no keyword unfound in 4 consecutive weeks; 3 keywords unfound in 2 of the last 4 |
| In the pack, latest week | 5 keywords, all at one location (LOC-005) |
| Position distribution | 95 in 1-3, 245 in 4-8, 991 past 8 |
| Near-pack (4-8 in 2+ of last 4 weeks) | 19 keywords across 5 locations |
| Lost the pack this window | 6 keywords (LOC-005) |
| Fell 3+ vs previous week | 13 keywords across 8 locations |
| Rival profiles | reviews 111-399 (median 269), rating 3.6-4.8, photos 25-141 (median 96) |
| Our profiles | reviews 14-260, rating 3.6-4.5, photos 3-61 |
| Search terms | 5 months (2026-04 to 2026-08); 230 of 501 terms appear in one month only |
| Terms losing 20%+ month over month, min 30 | 33 of 74 pairs (blanket) |
| Terms losing 50%+ month over month, min 200 | 18 of 55 pairs |

Lessons: a rule "keyword not in the pack" fails 107 of 112 keywords and tells nobody
anything. The pack-share rule stays as the headline (it is what the category is about),
but every other check is built to rank opportunity or name a specific cause.

## 3. The checks

| Rule | Fires when | Threshold (EngineConfig) | Why this threshold |
| --- | --- | --- | --- |
| `tracking_stale` | latest weekly check older than the window | `rank_freshness_days` 21 | Three missed weekly checks; then every rank rule abstains |
| `pack_share_low` | share of keywords in the pack in the latest week below the floor | `pack_share_min` 0.25 | One in four is the least a tuned profile should hold on its own terms |
| `pack_lost` | in the pack in an earlier trend week, not in the latest | `rank_trend_weeks` 4 | Regaining a spot is cheaper than earning one; 6 keywords in the fixture |
| `near_pack_opportunity` | positions 4-8 in 2+ of the last 4 weeks, not in the pack now | `near_pack_low` 4, `near_pack_high` 8, `near_pack_min_weeks` 2 | Two weeks filters single-week noise; 19 keywords in the fixture |
| `not_found_persistent` | not found in N consecutive weeks ending in the latest | `not_found_min_weeks` 4 | Four weeks rules out one bad crawl; zero in the fixture, by design |
| `rank_dropped` | latest position worse than the mean of the earlier trend weeks by N | `rank_drop_min_positions` 3 | Mean of three weeks removes the ±2 wobble |
| `high_intent_lagging` | high-intent keyword N behind the median of the other keywords, or not found | `high_intent_intents` (emergency, implants, orthodontics), `high_intent_lag_positions` 3 | Compares the money terms with the location's own baseline, so it discriminates |
| `branded_not_first` | keyword carrying a brand word not at position 1 (critical if not found) | none | Navigational query; any other result is a listing problem |
| `search_term_losing` | exact-month pair, earlier month at or above the floor, loss at or above the share | `term_loss_min_impressions` 200, `term_loss_share` 0.5 | Half the volume gone on a term that had real volume; 18 of 55 pairs in the fixture |
| `service_not_surfacing` | a project service none of the latest month's terms mention | none | Ties visibility to the operator's own service list |
| `rival_ahead_gap` | a rival ahead on N+ keywords in the latest week with 1.5x reviews, +0.3 rating or 1.5x photos | `rival_min_keywords_ahead` 3, `rival_review_ratio` 1.5, `rival_rating_gap` 0.3, `rival_photo_ratio` 1.5 | Rivals ahead on one keyword are noise; the gap must be clear, not marginal |

## 4. Data we have versus data we need

Have: weekly `rank_absolute`, `rank_in_local_pack`, `found` per tracked keyword; keyword
intent and device; three rivals per keyword-week with reviews, rating, photos; monthly
search terms with threshold flag; our own reviews and media summary for the comparison.

Need, not in the export: search volume per keyword (to weight opportunities by demand),
the grid or radius the tracker checked from (distance), the rival's categories and
services (relevance gap), and Google's own impressions per keyword. Without volume, all
near-pack keywords rank equally; the intent label is the only proxy.

## 5. Traps

- `rank_absolute` is `None` when not found: never coerce to 0 or a large number.
  `position()` returns `None` and every mean skips it.
- `is_threshold` rows carry a ceiling, not a count: never paired or charted.
- Consecutive weeks must be consecutive: `trend_weeks()` builds the slots from the
  latest week and a keyword missing a slot is not "not found", it is unchecked.
- Rivals are compared only within the same keyword and week, and only when we were
  checked on that keyword that week.
- Brand words exclude the trade words and the city, so "Brightpath Dental Plano" gives
  only "brightpath"; a keyword "cosmetic dentist plano" is not branded.
- The month of `as_of` is incomplete; the latest complete month is compared to the one
  before it, and the data must reach at least the month before that to count as current.
- One `assess` per rule, always, including when the rank tracker is stale.
