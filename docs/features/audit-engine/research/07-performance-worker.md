# Performance worker: research and check design

Status: 2026-09-14. Backs `backend/app/services/recommendations/categories/performance.py`.

## 1. What the Performance metrics are

Google's Business Profile Performance API reports one number per day per
[`DailyMetric`](https://developers.google.com/my-business/reference/performance/rest/v1/DailyMetric):

| Metric | Meaning |
| --- | --- |
| `BUSINESS_IMPRESSIONS_{DESKTOP,MOBILE}_{MAPS,SEARCH}` | Times the profile was shown, split by surface and device. Deduplicated per user per day. |
| `CALL_CLICKS` | Taps on the call button. |
| `WEBSITE_CLICKS` | Clicks through to the website link. |
| `BUSINESS_DIRECTION_REQUESTS` | Direction requests from the profile. |
| `BUSINESS_CONVERSATIONS` | Messages started from the profile (native chat retired July 2024; metric persists). |
| `BUSINESS_BOOKINGS` | Bookings via a Reserve with Google partner only; a self-supplied booking link reports nothing. |

Two things Google itself says, and the engine repeats in `contracts.SEMANTICS`:

- An action is an event, not a customer. One person can tap call three times; a
  direction request is not a visit; a website click is not a lead. The API counts
  interface events, so an "action rate" is an engagement ratio, never a conversion
  probability. (Performance API docs; also
  https://searchlab.nl/en/statistics/google-business-profile-statistics-2026, which
  reports ~5% of views leading to an action across listings.)
- A metric absent for a day is not zero. The API omits metrics it has no data for, and
  the store keeps them as NULL for the same reason (`models/performance.py`). A day with
  no row is unknown. Summing NULL as 0 manufactures a decline.

## 2. How practitioners read the numbers

- Trend over level. Industry audits (Search Engine Land local audit guide,
  https://searchengineland.com/guide/local-seo-audit) flag downtrends in calls,
  directions and bookings as symptoms of a listing or competitive problem, not the
  absolute count. Absolute benchmarks (BrightLocal insights study via searchlab.nl:
  median ~59 actions/month, mix ≈56% website / 24% calls / 20% directions) are for
  orientation only; they vary wildly by category and market.
- Compare like with like. Local businesses have a strong weekly cycle; in the sample
  data Saturday runs at ~45% and Sunday at ~15% of a weekday. A window that contains one
  more weekend than the previous one shows a phantom fall. The fix is to compare windows
  that are a multiple of 7 days long and to pair each day with the same weekday 28 days
  earlier.
- Surface and device splits are diagnostic, not good or bad. A shift from Search to
  Maps impressions usually means a change in how Google is matching the profile
  (category, name, pin, or a competitor now outranking on the branded query). A mobile
  share change with flat totals often tracks a Google interface change rather than
  anything the business did.
- What a drop usually means, in rough order of likelihood when investigating:
  1. Profile state: suspended, marked temporarily closed, hours changed or holiday hours
     set, pending edits reverted by Google (hours and status changes remove the profile
     from "open now" filters immediately).
  2. Identity change: primary category changed, name edited, address or pin moved; each
     re-triggers Google's relevance matching.
  3. Website or phone: site down, link changed to a redirect, call tracking number
     replaced (website clicks and calls fall while impressions hold).
  4. Competition: a new or upgraded competitor profile in the same block, a competitor
     running posts or gathering reviews (impressions fall, especially Maps).
  5. Demand and season: school terms, holidays, weather; visible as a fall across every
     location in the area, not this one alone.
  6. Reporting: Google occasionally back-fills or restates days; a partial trailing
     window always looks like a decline.
- Google says there is no way to buy ranking
  ([7091](https://support.google.com/business/answer/7091)) and behavioural signals are a
  minor and disputed ranking input. The worker therefore never promises that fixing a
  finding will raise impressions or revenue; it only says what fell and what to check.

## 3. What the data we hold supports

`performance_daily`: one row per location per day, 2026-06-15 to 2026-09-11 (89 days,
no gaps, no NULLs in the sample export; both are possible from the real API). Quick
stats over `locus-intelligence-assignment/data/location_daily_kpis.csv`:

| Location | Impr/day | Actions/impr | Maps share | Mobile share | Weekday means Mon..Sun | Last 28 vs prior 28 |
| --- | --- | --- | --- | --- | --- | --- |
| LOC-001 | 930 | 12.4% | 45% | 80% | 1159 1118 1178 1114 1156 524 171 | -2% |
| LOC-004 | 587 | 11.3% | 45% | 80% | 703 736 739 696 737 331 108 | -10% (calls -11%, directions -17%, website -12%) |
| LOC-006 | 419 | 12.5% | 45% | 80% | 523 497 529 503 528 236 77 | -10% (website -11%) |
| LOC-010 | 531 | 12.5% | 45% | 80% | 638 648 670 647 660 300 99 | +19% |
| LOC-012 | 85 | 12.6% | 45% | 80% | 104 100 106 105 108 47 16 | +10% |
| others | 131 to 1017 | 6.6% to 12.5% | 45% | 80% | same shape | within ±2% |

Take-aways that set the thresholds:

- Weekday pattern is strong and identical across locations: pairing by weekday is
  mandatory, and a 28-day window (four full weeks) is the natural unit.
- Even the smallest location has ~2,400 impressions and ~120 calls per 28 days, so a
  minimum of 200 paired impressions and 30 paired actions per window abstains only on
  genuinely thin profiles, never on the sample.
- Real movements in the sample sit at ±10%; noise between adjacent windows on flat
  locations is ±2%. A 10% reporting floor for impressions separates them. Actions are
  smaller counts and noisier, so their floor is 15%.
- Maps and mobile shares are stable to within a point across every location and
  window, so a 10-point shift is a genuine anomaly.
- The audit date defaults to today (2026-09-14) while the data ends 2026-09-11. Windows
  are anchored on the last day with data, not on as-of, so the current window is never
  partial; a freshness knob (14 days) abstains every trend check when the data is older
  than that instead of reporting a stale comparison as current.

Data we do not have and would want: Google's `BUSINESS_FOOD_*` metrics (not this
category), a change log of profile edits (to line a drop up with an edit date), fleet
or area-level demand to separate seasonality from a local problem, and website uptime.

## 4. The checks

All windows are `performance_window_days` (28) long, ending on the last day with data
on or before as-of. Previous window ends 28 days earlier. Days are paired by offset,
so each current day is compared to the same weekday four weeks before. A metric is
compared only on days where both paired rows report it as a number.

| Rule | Weight | Fires when | Abstains when | Score band |
| --- | --- | --- | --- | --- |
| `impressions_decline` | 3 | paired impressions fell ≥ `performance_impressions_decline` (10%) | stale, under 70% of days paired, or under 200 impressions in either window | graded 35 → 80 across 10% to 40% |
| `calls_decline` | 2 | paired call clicks fell ≥ `performance_actions_decline` (15%) | as above, or under 30 calls in previous window | graded 30 → 75 across 15% to 50% |
| `directions_decline` | 2 | same, direction requests | same | same |
| `website_clicks_decline` | 2 | same, website clicks | same | same |
| `action_rate_decline` | 2 | (calls + directions + website) / impressions fell ≥ `performance_action_rate_decline` (15%) relative | volume floors for both | graded 30 → 70 |
| `surface_split_shift` | 1 | Maps share of impressions moved ≥ `performance_split_shift_points` (0.10) either way | volume floor | 30 notice |
| `mobile_share_shift` | 1 | mobile share of impressions moved ≥ `performance_split_shift_points` | volume floor | 30 notice |
| `zero_action_days` | 2 | ≥ `performance_zero_action_streak_days` (3) consecutive days in the current window with ≥ `performance_zero_action_min_impressions` (20) impressions and every action reported as 0 | fewer evaluable days than the streak length, or stale | 55 warning, graded up with streak length |
| `data_gaps` | 1 | ≥ `performance_data_gap_days` (3) calendar days missing from the current window | no rows at all (nothing to measure a gap against), or stale | 20 notice |

Freshness: if the newest row is more than `performance_max_stale_days` (14) before
as-of, every check abstains with the age in the reason. A profile marked permanently
closed suppresses every check.

## 5. Traps this design avoids

- Unequal weekday mix: windows are 28 days and days are paired by offset.
- Partial current window: anchored on the last data day, never on today.
- Missing day as zero: a missing day is left out of both windows (its pair is dropped
  too), and the share of paired days must reach 70%.
- NULL metric as zero: each metric pairs independently; a NULL on either side drops
  that day for that metric only.
- Small numbers: 200 impressions and 30 actions floors before a percentage is computed.
- Zero-action streak needs impressions present that day, so "no data" never reads as
  "no one acted".
- Percentages of nothing: a previous value of 0 is never a denominator; the check
  abstains.
- Attribution: every finding says "descriptive change, not attribution" and the
  suggested plan is a checklist to investigate, ordered by likelihood, not a fix.
