# Reputation worker: research and check design

Status: 2026-09-14. Written before the worker was coded, per the engine rules.

## What the sources say

| Question | Finding | Source |
| --- | --- | --- |
| Rating customers act on | 38% of consumers require at least 4.0 (2025); 2026 summaries report a sharp rise in people who will only use a business at 4.5+ (31%, up from 17%) | [BrightLocal LCRS 2025](https://www.brightlocal.com/research/local-consumer-review-survey-2025/), [BrightLocal LCRS 2026](https://www.brightlocal.com/research/local-consumer-review-survey/), [PinMeTo summary](https://www.pinmeto.com/news/brightlocal-local-consumer-review-survey-2026/) |
| Review count | 10 reviews is a measurable ranking step; 47% of consumers will not use a business with fewer than 20 reviews; local-pack competitors set the bar | [Sterling Sky](https://www.sterlingsky.ca/number-of-reviews-impact-ranking/), [gbppromote summary](https://gbppromote.com/local-consumer-review-survey/) |
| Recency and velocity | Rankings soften after 3 to 4 weeks with no new review; 74% of consumers want a review from the last 3 months; target velocity is the top competitor's monthly rate plus one | [Whitespark](https://whitespark.ca/blog/the-most-underrated-local-ranking-factor-in-2025/), [Sterling Sky](https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/) |
| Reply rate | 89% expect a response; 80% more likely to use a business that answers every review; 42% unlikely to use one that never replies | [gbppromote summary](https://gbppromote.com/local-consumer-review-survey/) |
| Reply time | 2026: 19% expect same day, 32% next day, 81% within a week. 86% of complainers expect a reply within 3 days | [BrightLocal LCRS 2026](https://www.brightlocal.com/research/local-consumer-review-survey/), [GatherUp](https://gatherup.com/blog/software-to-reply-to-reviews-customer-feedback/), [ReplyOnTheFly study](https://www.replyonthefly.com/blog/google-review-response-time-study) |
| Reply quality | 50% are put off by generic, templated replies; 66% trust more when the business offers to make things right, 64% when the owner apologises | [PinMeTo summary](https://www.pinmeto.com/news/brightlocal-local-consumer-review-survey-2026/), [ReplyOnTheFly](https://www.replyonthefly.com/blog/google-review-response-time-study) |
| Google's reply guidance | Verify first. Be prompt, personal, short, conversational, not promotional. For negative reviews acknowledge, apologise where warranted, never share private details, offer to resolve offline, sign with a name or initials | [Manage customer reviews](https://support.google.com/business/answer/3474050), [Tips to get more reviews](https://support.google.com/business/answer/3474122), [Community guide](https://support.google.com/business/community-guide/318603570) |
| What not to do | No incentives, no gating, no soliciting on premises, no asking for specific content; fake or paid reviews are a negative ranking factor and consumers suspect them | [Maps contributed content policy](https://support.google.com/contributionpolicy/answer/7400114), [gmbapi factors](https://gmbapi.com/news/local-ranking-factors-comparison-2026-2023/) |

Google itself says "more reviews and positive ratings can help your business's local
ranking" and that replying "shows that you value their feedback"
([Ranking tips](https://support.google.com/business/answer/7091)).

## Data we have

`reviews` snapshot rows: `id`, `google_review_id`, `star_rating` (1 to 5 or null),
`comment`, `create_time`, `update_time`, `reply_comment`, `reply_update_time`,
`is_anonymous`. Reviewer name and photo are excluded from every snapshot.

`competitors` rows (via the location's tracked keywords): `review_count` and
`average_rating` per competitor per keyword-week.

Sample export, 12 locations, 1,514 reviews, 874 replies, as of 2026-09-11:

| Statistic | Range across locations |
| --- | --- |
| Reviews stored | 14 to 260 |
| Rating, all time | 3.64 to 4.52; last 90 days 2.75 to 4.58 |
| Change, last 90 days vs the 90 before | -1.63 (LOC-011), -0.55 (LOC-006), -0.53 (LOC-001) ... +1.14 (LOC-009) |
| Days since last review | 1 to 28 |
| Reviews in last 30 days | 1 to 23 |
| Reply rate | 0.07 to 0.97 (overall 0.58) |
| Reply rate on 1 to 3 star reviews | 0.12 to 1.00 (overall 0.54) |
| Median reply delay | 2 to 14 days (overall 3, p90 8, max 16) |
| Share of 1-star reviews | 0.00 to 0.23 |
| Competitor review count | median 276, range 111 to 460 |

No star rating is blank and no reply text is blank in the export, but the Google API
can deliver both, so the worker tolerates them.

## Checks to build

| Group | Rule | Weight | Fails when | Abstains when |
| --- | --- | --- | --- | --- |
| Rating | `rating_low` | 3 | mean rating over `rating_window_days` (90) below `rating_warning_min` (4.0); critical below `rating_critical_min` (3.5) | fewer than `min_reviews` (5) rated reviews in the window |
| Rating | `one_star_share_high` | 2 | share of 1-star reviews over `review_lookback_days` (365) above `one_star_share_max` (0.10) | fewer than `min_reviews` rated reviews |
| Trend | `rating_trend_falling` | 2 | mean rating of the last 90 days fell more than `rating_drop_max` (0.3) below the 90 before | either window has fewer than `min_reviews` |
| Volume | `reviews_few_vs_competitors` | 2 | stored review count below `competitor_review_ratio_min` (0.5) of the median competitor review count in the latest observed week | no competitor row with a review count |
| Recency | `no_recent_review` | 2 | days since the newest review above `review_gap_max_days` (30) | no reviews stored at all |
| Recency | `review_velocity_low` | 1 | reviews in the last 30 days below `reviews_per_month_min` (3) | no reviews stored at all |
| Responsiveness | `reply_rate_low` | 3 | replied share of reviews older than `reply_wait_days` (3) within the lookback below `reply_rate_min` (0.6) | fewer than `min_reviews` eligible |
| Responsiveness | `critical_reply_rate_low` | 2 | replied share of 1 to 3 star reviews older than `reply_wait_days` below `critical_reply_rate_min` (0.8) | fewer than `min_critical_reviews` (3) eligible |
| Responsiveness | `critical_review_unanswered` | 3 | any 1 to 3 star review older than `reply_wait_days` with no reply; one finding per review, newest first, at most `unanswered_list_max` (10) listed | no 1 to 3 star review older than the wait |
| Responsiveness | `reply_delay_high` | 2 | median days from review to reply above `reply_delay_max_days` (7) | fewer than `min_reviews` replied reviews with both dates |

Rationale for the numbers: 4.0 is the threshold the largest share of consumers name;
3.5 is where a profile drops out of every "4+" filter with margin. 30 days without a
review matches the 3 to 4 week ranking observation. 3 days is the complaint-reply window
consumers cite; 7 days is what 81% expect at most. A 60% reply rate sits at the sample
median, so half the sample fails and half passes, which is where an operating threshold
belongs; 80% on critical reviews reflects that complaints are the ones people read.
Half the competitor median is deliberately lenient: every sample location trails its
competitors on count, and the check should name the laggards, not everybody.

## Traps

- Reply state is current, not historical: a review replied to last week and one replied
  to the day it appeared look the same unless `reply_update_time` is present. Delay is
  computed only where both dates exist.
- Reviews are a self-selected sample. Rating and share checks describe what customers
  see, not the service quality.
- `star_rating` may be null: such rows are invalid for rating maths and excluded from
  every average, but still count as stored reviews for volume.
- `reply_comment` may be an empty string: blank means no reply.
- Absent rows are not zero: no reviews means abstain, never "zero velocity".
- Google's API only returns reviews the account can see; a count comparison with
  competitors compares stored rows with a scraped figure and is marked medium
  confidence.
- Competitor figures are per keyword-week; only the latest week per keyword is used and
  the median is taken across keywords so one crowded keyword cannot dominate.
- Findings must never carry a reviewer name. The subject is the Google review id.
