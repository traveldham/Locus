# Content worker: research notes

Status: 2026-09-14. Backs `backend/app/services/recommendations/categories/content.py`.
Covers photos, videos and posts. The logo and cover photo flags are already checked by
the profile worker (`logo_missing`, `cover_photo_missing`) and are not repeated here.

## 1. What the evidence says

### Photos: depth and mix

- Google's own ranking guidance lists "add photos and videos" among the ways to be more
  likely to show up, to "tell the story of your business", and names the photo types it
  wants: logo, cover, exterior, interior, products, team, at work. It publishes no count
  target. https://support.google.com/business/answer/7091 ;
  https://support.google.com/business/answer/6103862
- Google's widely cited figure: listings with photos get 42% more direction requests and
  35% more website clicks than listings without.
  https://newmedia.com/blog/google-business-profile-statistics
- BrightLocal's 45,264-listing study: listings with 100+ photos received +520% calls,
  +2,717% direction requests and +1,065% website clicks versus the average listing; the
  median listing had 11 photos. https://www.vendasta.com/blog/google-business-photos/ ;
  https://searchlab.nl/en/statistics/google-business-profile-statistics-2026
  Caveat: correlation. Busy, established businesses accumulate customer photos and also
  get more calls; the study cannot separate the two, and the 100+ tier is dominated by
  hospitality and retail. It supports "more and varied photos help conversion", not a
  specific count causing lift.
- Sterling Sky's "near me" study found photo volume had negligible ranking effect in a
  non-visual industry (garage doors) while strongly affecting conversion.
  https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/
- Photo rules: JPG or PNG, 10 KB to 5 MB, 720 x 720 recommended, in focus, well lit,
  no heavy filters. Videos: up to 30 seconds, 75 MB, 720p or higher.
  https://support.google.com/business/answer/6103862

Reading: depth matters as a conversion factor, mix matters because each type answers a
different customer question (exterior: can I find it; interior: what is it like inside;
team: who will treat me). A zero in any of the three named types is a gap a manager can
close in an afternoon.

### Upload recency

No official target. Industry audits (Search Engine Land, Search Engine Journal) list
"regularly add new photos" as a hygiene item, and the consumer surveys behind the
reputation notes (74% want reviews from the last three months) point at the same
expectation of a living profile. A quarter without a new photo is the working floor.

### Posts: cadence, expiry, CTA

- Google archives posts older than six months unless a date range is set; offers and
  events carry start and end dates and disappear from the profile when they lapse.
  https://support.google.com/business/answer/7342169
- Post types via API: STANDARD (update), EVENT, OFFER, ALERT. CTA types include BOOK,
  ORDER, SHOP, LEARN_MORE, SIGN_UP, CALL. Offers get an automatic "View offer" button.
  https://developers.google.com/my-business/reference/rest/v4/accounts.locations.localPosts
- Content rules: professional and family friendly; no phone numbers in the description
  (posts may be rejected); no misspellings, extra characters, gimmicky or auto-generated
  text that adds no value; regulated products excluded.
  https://support.google.com/business/answer/7662907
- Posts do not move local-pack rank. Sterling Sky posted weekly for nine weeks on three
  listings tracking 441 keywords and saw "no noticeable change in rankings". Posts are
  for conversion: they show on the profile and give a customer a next step.
  https://www.sterlingsky.ca/do-google-posts-impact-ranking/
- Industry checklists recommend weekly posting; the six-month archive means a profile
  that stops posting looks empty within two quarters.

Reading: score posts as conversion hygiene, never as a ranking claim. Cadence, a mix of
types and a call to action are the observable proxies.

## 2. What the sample data shows (as of 2026-09-14)

`location_media_summary.csv`, 12 rows:

- Photo counts: 3, 4, 7, 12, 15, 18, 26, 28, 32, 34, 44, 61. Median 22.
- Empty types: LOC-007 has zero interior and zero team photos; six locations have no
  video.
- Days since last upload: 16 to 75 for eleven locations; LOC-007 at 284 days.
- No location is missing its media row and no count is null, but the model allows both.

`posts.csv`, 69 posts, 2026-03-01 to 2026-09-07:

- Three locations (LOC-002, LOC-009, LOC-012) have no posts at all.
- Days since last post for the rest: 7, 12, 13, 23, 33, 44, 54, 61, 138.
- Posts in the last 90 days: 11, 7, 5, 2, 2, 2, 2, 2, 0.
- Type mix overall: 29 standard, 23 offer, 17 event. Every posting location uses at
  least two types.
- 12 of 69 posts have no CTA; per location the share ranges 0 to 33%.
- Summaries are short (max 47 characters). No offer or event dates are exported.

## 3. Checks

| Rule | Severity | Threshold (EngineConfig) | Rationale |
| --- | --- | --- | --- |
| `photos_few` | warning | `content_photo_floor` = 10 | Below the industry median of 11; three sample locations sit here |
| `photos_below_target` | notice | `content_photo_target` = 30 | A working target above the sample median; the 100+ tier is a stretch goal, not a floor |
| `photo_type_empty` | warning, one per type | zero interior, exterior or team | Each named type answers a customer question |
| `video_missing` | notice | zero videos | Google asks for video; a notice because many good profiles have none |
| `photos_stale` | warning | `content_photo_stale_days` = 90 | A quarter without a new photo |
| `posts_none_recent` | warning (critical when never posted) | `content_post_gap_days` = 30 | Weekly is the recommendation; a month is the floor |
| `posts_sparse` | warning | `content_posts_min_90d` = 6 | About one every two weeks |
| `post_types_uniform` | notice | all one type across `content_post_mix_min_posts` = 3 or more posts in the 180-day window | Offers and events are the types with a built-in button and a date |
| `posts_without_cta` | notice | share without CTA above `content_post_cta_max_missing_share` = 0.5 | A post without a next step is a missed click |

Window: `content_post_window_days` = 180 mirrors Google's six-month archive, so the
audit sees what a customer can still see.

Not built: "expired offer or event is still the latest post". The export carries no
event or offer dates, so it cannot be judged; it needs the LocalPost API's `event.schedule`
and `offer` fields.

## 4. Data we have versus data we need

| Have | Need for a stronger check |
| --- | --- |
| Photo counts by type (rollup) | The media items themselves: upload time per item, who uploaded (owner vs customer), dimensions, to judge quality and ownership |
| `last_photo_uploaded_on` | Per-item timestamps, to see cadence not just recency |
| Post type, summary, CTA, publish date | Post views and CTA clicks (the API has none today), event and offer dates, post state (live, rejected) |

## 5. Traps

- An absent media row is unknown, not zero. Every photo check abstains.
- A null count (for example `team_photo_count` null) is unknown for that type only; the
  other types are still judged.
- `last_photo_uploaded_on` null with photos present means the export did not carry the
  date; abstain rather than call the photos stale.
- An incomplete export looks exactly like a posting gap. A location with zero post rows
  is reported as never posted with medium confidence and a limitation that says so.
- Post enum values arrive lower-case from the model (`standard`, `offer`) but upper-case
  in the raw CSV; the worker casefolds.
- The analysis date can be after the last export date (posts end 2026-09-07, audits run
  2026-09-14), so "days since" figures include the export lag.
