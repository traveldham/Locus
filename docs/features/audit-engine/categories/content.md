# Content worker

Category `content`, weight 10. Module: `backend/app/services/recommendations/categories/content.py`.
Suggestion layer: `backend/app/services/recommendations/suggestions/content.py`.
Research: `docs/features/audit-engine/research/08-content-worker.md`.

## What it answers

Does the profile show customers what the place looks like, and does it say anything new?
Two groups of checks. Every check is deterministic. A permanently closed profile
suppresses every check. Posts are scored as conversion hygiene: they do not move rank
(Sterling Sky's nine-week test), they move clicks. The logo and cover photo flags are
checked by the profile worker and are not repeated here.

| Group | Rule | Weight | Severity | Fails when | Abstains when |
| --- | --- | --- | --- | --- | --- |
| Photos | `photos_few` | 3 | warning | `photo_count` below `content_photo_floor` (10) | no media row, or count null |
| Photos | `photos_below_target` | 1 | notice | count at or above the floor but below `content_photo_target` (30) | as above; suppressed when already below the floor |
| Photos | `photo_type_empty` | 2 | warning | interior, exterior or team count is zero, one finding per type | no media row, or every type count null; a null type is skipped, not judged |
| Photos | `video_missing` | 1 | notice | `video_count` is zero | no media row, or count null |
| Photos | `photos_stale` | 2 | warning | days since `last_photo_uploaded_on` over `content_photo_stale_days` (90) | no media row, or date null; suppressed when there are no photos at all |
| Posts | `posts_none_recent` | 3 | warning; critical when no post exists | days since the latest post over `content_post_gap_days` (30), or zero post rows (medium confidence) | never |
| Posts | `posts_sparse` | 2 | warning | posts in the last 90 days below `content_posts_min_90d` (6) | suppressed when there are none in 90 days, or no posts at all: the gap check owns that |
| Posts | `post_types_uniform` | 1 | notice | every post in the `content_post_window_days` (180) window is one type | fewer than `content_post_mix_min_posts` (3) posts in the window |
| Posts | `posts_without_cta` | 1 | notice | share of posts in the window with no CTA above `content_post_cta_max_missing_share` (0.5) | fewer than `content_post_mix_min_posts` posts in the window |

Semantics that matter:

- The media summary is a rollup of counts, not the photos. An absent row is unknown and
  abstains every photo check. A null count is unknown for that check only.
- Photo type counts need not sum to the total; the remainder is uncategorised and is
  reported on the card as "other".
- Posts are events. Zero rows over a window is an observation, reported with medium
  confidence and a limitation saying an incomplete export looks the same.
- Post type and CTA values are casefolded, so the raw export's `STANDARD` and the
  model's `standard` are one thing. Posts with no readable publish date are ignored.
- The 180-day window mirrors Google's six-month post archive: the audit judges what a
  customer can still see.
- Every threshold is a field on `EngineConfig` under `# ---- content worker ----` and is
  an operating policy. Google publishes no photo count or posting cadence.
- "Days since" figures run to the analysis date, which may be after the last export.

Not built: an expired offer or event still being the latest post. The export carries no
event or offer dates; it needs the LocalPost API's schedule fields.

## Card

`card(snapshot)` returns, for the category view:

- `photos`: total, interior, exterior, team, other (total minus the typed counts),
  videos, last upload date and days since it.
- `posts`: total, count in the last 90 days, last post date and type and days since,
  type mix and CTA share over the last 180 days, and the last five posts (type, date,
  summary first 120 characters, CTA).

The snapshot carries no analysis date, so the card counts days from today; it is display
only and never feeds a verdict. Frontend: `frontend/src/components/recommendations/cards/content-card.tsx`
exports `ContentCard` (photo coverage bars, tiles, a post timeline, and the drafts).

## Suggestions

After the checks run, the worker task asks the configured model for one draft per finding
whose check declares a `suggests` field:

| Check | Field drafted | Shape |
| --- | --- | --- |
| `posts_none_recent`, `posts_sparse`, `post_types_uniform`, `posts_without_cta` | `post_drafts` | a list of exactly two posts, one update and one offer or event, each under 300 characters, ending with the button it should carry |
| `photos_few`, `photos_below_target`, `photo_type_empty` | `photo_shot_list` | a list of five to eight specific shots, each under 120 characters, matched to the empty type and the category |

The prompt carries the profile basics, the photo counts, the last five posts and every
project the location belongs to (name, description, services), so drafts are about this
business. Enforced in code, regardless of the model: no URLs or email addresses, no phone
numbers, no word of four or more letters in ALL CAPS, length caps, exactly two post
drafts, five to eight distinct shots, one suggestion per finding, and the field must match
the rule. A draft set that loses a member to those rules is dropped whole rather than
attached half-finished. `fallback_summary` is deterministic.

## Tests

- `backend/tests/test_content_worker.py`: every check declared and assessed once, a
  complete profile scores 100, absent media row abstains, null counts abstain only their
  own check, and one mutation per check flips its verdict; the card shape.
- `backend/tests/test_content_suggestions.py`: target selection, context and prompt
  content, attachment and validation of drafts, rule enforcement, skip conditions.
