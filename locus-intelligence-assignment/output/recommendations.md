# Location audit

Analysis date: 2026-09-11
Engine: 2.0.0
Profiles audited: 12

## Fleet health `##############......` 70/100 (fair)

12 of 12 locations scored. 180 open issues: 22 critical, 134 warning, 24 notice.

Weighted share of evaluated checks that passed, reduced by each failing check's severity and by the share of the subjects it examined that failed. Checks without enough evidence are excluded from the score, never counted as passes.

### Issues by category

| Category | Weight | Avg score | Issues | Locations | Worst |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 20 | 82 | 14 | 12 | critical |
| Reputation | 20 | 86 | 3 | 3 | critical |
| Local visibility | 25 | 48 | 136 | 12 | warning |
| Operations | 15 | 41 | 17 | 11 | critical |
| Performance | 10 | 98 | 1 | 1 | notice |
| Content | 10 | 87 | 9 | 8 | warning |

### Lowest scoring locations

- Brightpath Dental — Irving: 60/100
- Brightpath Dental — Round Rock: 62/100
- Brightpath Dental — Deep Ellum: 63/100
- Brightpath Dental — Chandler Ocotillo: 69/100
- Brightpath Dental — Katy: 69/100

## LOC-006 - Brightpath Dental — Irving

Health `############........` 60/100 (fair). 2 checks passed, 7 failed, 1 not evaluated (90% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 47 | 0 | 1 | 0 | 1 |
| Local visibility | 45 | 0 | 2 | 0 | 13 |
| Operations | 42 | 0 | 1 | 1 | 1 |
| Performance | 75 | 0 | 1 | 0 | 1 |
| Content | 70 | 1 | 1 | 0 | 1 |

Metrics:

- Impressions (28d): 10217 (-10.0% vs previous window)
- Customer actions (28d): 1297 (-7.9% vs previous window)
- Actions per impression: 12.69% (+2.3% vs previous window)
- Average rating (90d): 4 stars
- Reviews received (90d): 20
- Reviews with a reply: 45%
- Unanswered reviews rated 1-3: 2
- Keywords tracked: 10
- Keywords in the local pack: 0%
- Average position where found: 9.6
- Settled past visits (90d): 19
- Cancelled or no-show: 47.4%
- Requests still marked new (28d): 7
- Days since last post: 135 days

### [critical] Reconcile outstanding appointment requests

Operations - score 94/100. Evidence confidence: high.

7 of 24 recent requests still say new after at least 2 days. The oldest was created 25 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 7, "recent_requests": 24, "oldest_age_days": 25, "wait_days": 2}`. 7 source records (IDs and full rows in JSON).

### [critical] Respond to unanswered critical reviews

Reputation - score 77/100. Evidence confidence: high.

2 reviews rated 1-3 remain unanswered after 3 days, among 9 recent reviews (22%). The oldest has waited 24 days.

Read the flagged reviews, acknowledge the concern without sharing customer details, and invite private follow-up. Investigate recurring issues internally.

Limit: Reply state is current; reviews are a self-selected sample. No automatic public reply is sent.

- reviews: Count rating <= 3, reply absent, age >= wait days. Values: `{"unanswered": 2, "pending_row_ids": ["0b5dbb05-1a58-480b-b06f-cc09f1cc0bd6", "ec6b6549-ff51-4682-8a95-55a76e16a734"], "recent_reviews": 9, "unanswered_share": 0.2222, "oldest_wait_days": 24, "wait_days": 3}`. 9 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 4.

Check the result URL and listing relevance for “cosmetic dentist irving” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 4}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist irving", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Irving Dental Clinic", "rank_absolute": 2, "review_count": 219, "average_rating": 4.3, "photo_count": 54}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “dental implants irving” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants irving", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Dallas Dental Excellence", "rank_absolute": 10, "review_count": 343, "average_rating": 4.8, "photo_count": 58}, {"competitor_name": "Irving Dental Clinic", "rank_absolute": 5, "review_count": 231, "average_rating": 4.3, "photo_count": 51}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 5.

Check the result URL and listing relevance for “dentist irving” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 5}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist irving", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Dallas Dental Excellence", "rank_absolute": 4, "review_count": 331, "average_rating": 4.8, "photo_count": 58}, {"competitor_name": "Northgate Emergency Dental", "rank_absolute": 4, "review_count": 216, "average_rating": 4.7, "photo_count": 95}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist irving tx”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 5.

Check the result URL and listing relevance for “dentist irving tx” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist irving tx", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 5}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist irving tx", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Dallas Dental Excellence", "rank_absolute": 3, "review_count": 343, "average_rating": 4.8, "photo_count": 60}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dental care irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “emergency dental care irving” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dental care irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dental care irving", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Northgate Emergency Dental", "rank_absolute": 3, "review_count": 264, "average_rating": 4.7, "photo_count": 94}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “emergency dentist irving” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist irving", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Northgate Emergency Dental", "rank_absolute": 2, "review_count": 264, "average_rating": 4.7, "photo_count": 94}, {"competitor_name": "Dallas Dental Excellence", "rank_absolute": 8, "review_count": 367, "average_rating": 4.8, "photo_count": 60}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist irving tx”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “emergency dentist irving tx” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist irving tx", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist irving tx", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Northgate Emergency Dental", "rank_absolute": 2, "review_count": 264, "average_rating": 4.7, "photo_count": 95}, {"competitor_name": "Irving Family Care Dentistry", "rank_absolute": 8, "review_count": 287, "average_rating": 3.8, "photo_count": 154}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 8.

Check the result URL and listing relevance for “invisalign irving” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 8}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign irving", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Irving Family Care Dentistry", "rank_absolute": 8, "review_count": 323, "average_rating": 3.8, "photo_count": 151}, {"competitor_name": "Northgate Emergency Dental", "rank_absolute": 7, "review_count": 228, "average_rating": 4.7, "photo_count": 93}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 7.

Check the result URL and listing relevance for “pediatric dentist irving” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 7}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist irving", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Dallas Dental Excellence", "rank_absolute": 3, "review_count": 355, "average_rating": 4.8, "photo_count": 58}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening irving”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “teeth whitening irving” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening irving", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening irving", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Irving Dental Clinic", "rank_absolute": 12, "review_count": 231, "average_rating": 4.3, "photo_count": 56}, {"competitor_name": "Northgate Emergency Dental", "rank_absolute": 6, "review_count": 240, "average_rating": 4.7, "photo_count": 93}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath dental”

Local visibility - score 68/100. Evidence confidence: medium.

“brightpath dental” fell 80%, from 1,510 (2026-07) to 307 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental", "previous": 1510, "current": 307, "lost_impressions": 1203, "decline_share": 0.7967, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “emergency dentist”

Local visibility - score 68/100. Evidence confidence: medium.

“emergency dentist” fell 99%, from 642 (2026-07) to 7 impressions (2026-08).

Inspect the listing and relevant website page for “emergency dentist”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "emergency dentist", "previous": 642, "current": 7, "lost_impressions": 635, "decline_share": 0.9891, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “tooth extraction”

Local visibility - score 67/100. Evidence confidence: medium.

“tooth extraction” fell 59%, from 568 (2026-07) to 233 impressions (2026-08).

Inspect the listing and relevant website page for “tooth extraction”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "tooth extraction", "previous": 568, "current": 233, "lost_impressions": 335, "decline_share": 0.5898, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Check whether a useful customer update is overdue

Content - score 45/100. Evidence confidence: medium.

The last recorded post was 135 days before the analysis date, past the 45-day policy window.

Confirm the post history is current; publish an accurate update only if there is useful news, a real event or an available offer.

Limit: An incomplete export can explain the gap. Posting cadence is not a rank factor established by this dataset.

- posts: as_of minus latest published_on. Values: `{"gap_days": 135, "threshold_days": 45}`. 1 source records (IDs and full rows in JSON).

### [notice] Investigate a recent performance decline

Performance - score 38/100. Evidence confidence: medium.

Impressions fell 10.0%, from 11,353 to 10,217. Compared 28 matched days in consecutive 28-day windows.

Review the affected dates and device/surface split. Check listing accuracy, website and phone availability, and local demand before selecting a remedy.

Limit: Descriptive change, not attribution. Actions can repeat per customer and are not a conversion rate. Seasonality and partial reporting may contribute.

- performance: Matched offsets: sum impressions; actions / impressions; (previous - current) / previous. Values: `{"current_impressions": 10217, "previous_impressions": 11353, "impression_change": -0.100062, "current_actions": 1297, "previous_actions": 1408, "action_rate_change": 0.023587, "matched_days": 28, "window_days": 28, "current_start": "2026-08-15", "current_end": "2026-09-11", "previous_start": "2026-07-18", "previous_end": "2026-08-14", "reporting_floor": 0.1, "warning_fraction": 0.2}`. 56 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 31/100. Evidence confidence: medium.

10 of 34 category attributes are unset (29%).

Review these available attributes; record true or false only after confirmation: wheelchair_accessible_parking, lgbtq_friendly, appointment_required, accepts_debit_cards, transgender_safespace, has_onsite_parking, sedation_available, emergency_services, identifies_as_veteran_owned, mask_required.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 10, "unset_share": 0.2941, "missing": ["wheelchair_accessible_parking", "lgbtq_friendly", "appointment_required", "accepts_debit_cards", "transgender_safespace", "has_onsite_parking", "sedation_available", "emergency_services", "identifies_as_veteran_owned", "mask_required"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 24}`. 24 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 10 of 34 category attributes are unset.
- media: clear - No explicitly missing profile or cover image.
- posts: triggered - Last recorded post was 135 days ago.
- reviews: triggered - 2 of 9 recent reviews rated 1-3 are unanswered.
- booking_followup: triggered - 7 requests still say new after 2 days.
- booking_outcomes: insufficient_data - Fewer than 20 settled past visits in 90 days (19).
- performance: triggered - Impressions fell 10.0%, from 11,353 to 10,217.
- search: triggered - 3 of 5 matched terms fell at least 20%, losing 2,173 impressions.
- rankings: triggered - 10 of 10 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-003 - Brightpath Dental — Round Rock

Health `############........` 62/100 (fair). 3 checks passed, 6 failed, 1 not evaluated (90% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 19 | 0 | 2 | 0 | 2 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 50 | 0 | 2 | 0 | 9 |
| Operations | 48 | 0 | 1 | 1 | 1 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 88 | 1 | 1 | 0 | 1 |

Metrics:

- Impressions (28d): 10143 (-0.3% vs previous window)
- Customer actions (28d): 1045 (+0.0% vs previous window)
- Actions per impression: 10.3% (+0.2% vs previous window)
- Average rating (90d): 4.58 stars
- Reviews received (90d): 26
- Reviews with a reply: 50%
- Unanswered reviews rated 1-3: 1
- Keywords tracked: 8
- Keywords in the local pack: 0%
- Average position where found: 10.8
- Settled past visits (90d): 17
- Cancelled or no-show: 52.9%
- Requests still marked new (28d): 4
- Days since last post: 41 days

### [critical] Reconcile outstanding appointment requests

Operations - score 94/100. Evidence confidence: high.

4 of 20 recent requests still say new after at least 2 days. The oldest was created 25 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 4, "recent_requests": 20, "oldest_age_days": 25, "wait_days": 2}`. 4 source records (IDs and full rows in JSON).

### [critical] Confirm and complete customer-facing information

Profile completeness - score 84/100. Evidence confidence: high.

2 essential profile fields need confirmation, including website_uri.

Check the missing fields with the location manager, then update only confirmed information: website_uri, description.

Limit: This is current stored profile state; no historical reconstruction. No claim that completing fields improves rank.

- locations: Missing or unverified fields in current profile. Values: `{"missing_fields": ["website_uri", "description"], "urgent_fields": ["website_uri"]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “cosmetic dentist round rock” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist round rock", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Round Rock Dental Studio", "rank_absolute": 7, "review_count": 156, "average_rating": 3.6, "photo_count": 82}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “dental implants round rock” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants round rock", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Heritage Dental Group", "rank_absolute": 8, "review_count": 291, "average_rating": 4.2, "photo_count": 133}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist open saturday round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “dentist open saturday round rock” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist open saturday round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist open saturday round rock", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Prime Care Dentistry", "rank_absolute": 10, "review_count": 414, "average_rating": 4.4, "photo_count": 130}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “dentist round rock” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist round rock", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Heritage Dental Group", "rank_absolute": 8, "review_count": 291, "average_rating": 4.2, "photo_count": 138}, {"competitor_name": "Prime Care Dentistry", "rank_absolute": 10, "review_count": 426, "average_rating": 4.4, "photo_count": 129}, {"competitor_name": "Round Rock Dental Studio", "rank_absolute": 7, "review_count": 180, "average_rating": 3.6, "photo_count": 82}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 7.

Check the result URL and listing relevance for “emergency dentist round rock” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 7}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist round rock", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Prime Care Dentistry", "rank_absolute": 8, "review_count": 390, "average_rating": 4.4, "photo_count": 126}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “invisalign round rock” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign round rock", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Heritage Dental Group", "rank_absolute": 8, "review_count": 303, "average_rating": 4.2, "photo_count": 135}, {"competitor_name": "Prime Care Dentistry", "rank_absolute": 7, "review_count": 426, "average_rating": 4.4, "photo_count": 127}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 7.

Check the result URL and listing relevance for “pediatric dentist round rock” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 7}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist round rock", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Heritage Dental Group", "rank_absolute": 4, "review_count": 327, "average_rating": 4.2, "photo_count": 136}, {"competitor_name": "Prime Care Dentistry", "rank_absolute": 10, "review_count": 414, "average_rating": 4.4, "photo_count": 130}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening round rock”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “teeth whitening round rock” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening round rock", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening round rock", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “dentist open sunday”

Local visibility - score 55/100. Evidence confidence: medium.

“dentist open sunday” fell 40%, from 1,176 (2026-07) to 700 impressions (2026-08).

Inspect the listing and relevant website page for “dentist open sunday”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "dentist open sunday", "previous": 1176, "current": 700, "lost_impressions": 476, "decline_share": 0.4048, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Add missing profile imagery

Content - score 40/100. Evidence confidence: high.

The photo summary explicitly marks these images as missing: has_cover_photo.

Ask the manager for accurate, current imagery for: has_cover_photo. Review before uploading.

Limit: Counts cannot establish photo quality; no ranking uplift is inferred.

- media: Explicit false image flags. Values: `{"missing": ["has_cover_photo"]}`. 1 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 34/100. Evidence confidence: medium.

15 of 34 category attributes are unset (44%).

Review these available attributes; record true or false only after confirmation: accepts_insurance, teeth_whitening, online_appointments, digital_xray, has_restroom, orthodontic_care, gender_neutral_restroom, tv_in_waiting_area, accepts_new_patients, walk_ins_welcome, saturday_appointments, wheelchair_accessible_entrance, identifies_as_women_owned, identifies_as_veteran_owned, mask_required.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 15, "unset_share": 0.4412, "missing": ["accepts_insurance", "teeth_whitening", "online_appointments", "digital_xray", "has_restroom", "orthodontic_care", "gender_neutral_restroom", "tv_in_waiting_area", "accepts_new_patients", "walk_ins_welcome", "saturday_appointments", "wheelchair_accessible_entrance", "identifies_as_women_owned", "identifies_as_veteran_owned", "mask_required"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 19}`. 19 source records (IDs and full rows in JSON).

Coverage:

- profile: triggered - 2 essential fields need confirmation.
- attributes: triggered - 15 of 34 category attributes are unset.
- media: triggered - 1 profile images are explicitly marked missing.
- posts: clear - A post falls within the configured recency window.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: triggered - 4 requests still say new after 2 days.
- booking_outcomes: insufficient_data - Fewer than 20 settled past visits in 90 days (17).
- performance: clear - Largest measured fall 0.3% is below the 10% reporting floor.
- search: triggered - 1 of 5 matched terms fell at least 20%, losing 476 impressions.
- rankings: triggered - 8 of 8 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-004 - Brightpath Dental — Deep Ellum

Health `#############.......` 63/100 (fair). 3 checks passed, 7 failed, 0 not evaluated (100% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 47 | 0 | 1 | 0 | 1 |
| Local visibility | 49 | 0 | 2 | 0 | 11 |
| Operations | 25 | 0 | 2 | 0 | 2 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 88 | 1 | 1 | 0 | 1 |

Metrics:

- Impressions (28d): 14849 (-9.6% vs previous window)
- Customer actions (28d): 1553 (-13.1% vs previous window)
- Actions per impression: 10.46% (-4.0% vs previous window)
- Average rating (90d): 3.9 stars
- Reviews received (90d): 49
- Reviews with a reply: 6.1%
- Unanswered reviews rated 1-3: 13
- Keywords tracked: 9
- Keywords in the local pack: 0%
- Average position where found: 13.1
- Settled past visits (90d): 25
- Cancelled or no-show: 40%
- Requests still marked new (28d): 4
- Days since last post: 58 days

### [critical] Reconcile outstanding appointment requests

Operations - score 94/100. Evidence confidence: high.

4 of 25 recent requests still say new after at least 2 days. The oldest was created 23 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 4, "recent_requests": 25, "oldest_age_days": 23, "wait_days": 2}`. 4 source records (IDs and full rows in JSON).

### [critical] Respond to unanswered critical reviews

Reputation - score 81/100. Evidence confidence: high.

4 reviews rated 1-3 remain unanswered after 3 days, among 18 recent reviews (22%). The oldest has waited 25 days.

Read the flagged reviews, acknowledge the concern without sharing customer details, and invite private follow-up. Investigate recurring issues internally.

Limit: Reply state is current; reviews are a self-selected sample. No automatic public reply is sent.

- reviews: Count rating <= 3, reply absent, age >= wait days. Values: `{"unanswered": 4, "pending_row_ids": ["86fcf223-b7d9-48be-9baa-b56024f6caf6", "8e5340c9-5913-487f-bfc8-5e4feebb166f", "93c8b4fe-fddf-441d-8b36-473f9038d816", "97312f9d-763c-4cc8-8328-266c13fdf78d"], "recent_reviews": 18, "unanswered_share": 0.2222, "oldest_wait_days": 25, "wait_days": 3}`. 18 source records (IDs and full rows in JSON).

### [critical] Review cancellation and no-show follow-up

Operations - score 78/100. Evidence confidence: medium.

10 of 25 settled past visits were cancelled or no-show (40.0%) over 90 days, against a 20% policy threshold.

Audit the flagged past appointments and reminder process with the manager. Check cancellation reasons before deciding whether to change reminders.

Limit: Excludes future appointments and unsettled statuses; excludes unknown outcomes. The threshold is a configurable operating policy, not an industry benchmark.

- bookings: (cancelled + no_show) / settled past visits. Values: `{"failed": 10, "cancelled": 8, "no_show": 2, "settled": 25, "rate": 0.4, "window_days": 90, "threshold": 0.2}`. 25 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “cosmetic dentist dallas” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist dallas", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “dental implants dallas” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants dallas", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Dallas Family Dentistry", "rank_absolute": 6, "review_count": 281, "average_rating": 3.9, "photo_count": 118}, {"competitor_name": "Prestige Dental Studio", "rank_absolute": 12, "review_count": 184, "average_rating": 3.8, "photo_count": 94}, {"competitor_name": "SmileWorks Dental", "rank_absolute": 9, "review_count": 426, "average_rating": 3.8, "photo_count": 100}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 12.

Check the result URL and listing relevance for “dentist dallas” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 12}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist dallas", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist deep ellum”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “dentist deep ellum” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist deep ellum", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist deep ellum", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Dallas Family Dentistry", "rank_absolute": 14, "review_count": 269, "average_rating": 3.9, "photo_count": 115}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “emergency dentist dallas” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist dallas", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Deep Ellum Dental Care", "rank_absolute": 13, "review_count": 233, "average_rating": 4.4, "photo_count": 66}, {"competitor_name": "Dallas Family Dentistry", "rank_absolute": 12, "review_count": 281, "average_rating": 3.9, "photo_count": 119}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “invisalign dallas” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign dallas", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “pediatric dentist dallas” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist dallas", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Prestige Dental Studio", "rank_absolute": 11, "review_count": 184, "average_rating": 3.8, "photo_count": 92}, {"competitor_name": "Dallas Family Dentistry", "rank_absolute": 16, "review_count": 293, "average_rating": 3.9, "photo_count": 115}, {"competitor_name": "Deep Ellum Dental Care", "rank_absolute": 9, "review_count": 209, "average_rating": 4.4, "photo_count": 61}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 8.

Check the result URL and listing relevance for “teeth whitening dallas” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 8}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening dallas", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "SmileWorks Dental", "rank_absolute": 12, "review_count": 426, "average_rating": 3.8, "photo_count": 99}, {"competitor_name": "Dallas Family Dentistry", "rank_absolute": 11, "review_count": 293, "average_rating": 3.9, "photo_count": 118}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “walk in dentist dallas”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 14.

Check the result URL and listing relevance for “walk in dentist dallas” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "walk in dentist dallas", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 14}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "walk in dentist dallas", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Northpoint Dental Associates", "rank_absolute": 14, "review_count": 294, "average_rating": 3.8, "photo_count": 66}, {"competitor_name": "Dallas Family Dentistry", "rank_absolute": 16, "review_count": 281, "average_rating": 3.9, "photo_count": 119}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath deep ellum”

Local visibility - score 64/100. Evidence confidence: medium.

“brightpath deep ellum” fell 54%, from 3,280 (2026-07) to 1,520 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath deep ellum”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath deep ellum", "previous": 3280, "current": 1520, "lost_impressions": 1760, "decline_share": 0.5366, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Lost search visibility for “brightpath dental dallas”

Local visibility - score 44/100. Evidence confidence: medium.

“brightpath dental dallas” fell 23%, from 1,025 (2026-07) to 786 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental dallas”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental dallas", "previous": 1025, "current": 786, "lost_impressions": 239, "decline_share": 0.2332, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 31/100. Evidence confidence: medium.

11 of 34 category attributes are unset (32%).

Review these available attributes; record true or false only after confirmation: implant_services, wheelchair_accessible_parking, wifi_available, has_restroom, orthodontic_care, language_assistance, transgender_safespace, accepts_new_patients, walk_ins_welcome, emergency_services, kids_area.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 11, "unset_share": 0.3235, "missing": ["implant_services", "wheelchair_accessible_parking", "wifi_available", "has_restroom", "orthodontic_care", "language_assistance", "transgender_safespace", "accepts_new_patients", "walk_ins_welcome", "emergency_services", "kids_area"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 23}`. 23 source records (IDs and full rows in JSON).

### [notice] Check whether a useful customer update is overdue

Content - score 31/100. Evidence confidence: medium.

The last recorded post was 58 days before the analysis date, past the 45-day policy window.

Confirm the post history is current; publish an accurate update only if there is useful news, a real event or an available offer.

Limit: An incomplete export can explain the gap. Posting cadence is not a rank factor established by this dataset.

- posts: as_of minus latest published_on. Values: `{"gap_days": 58, "threshold_days": 45}`. 1 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 11 of 34 category attributes are unset.
- media: clear - No explicitly missing profile or cover image.
- posts: triggered - Last recorded post was 58 days ago.
- reviews: triggered - 4 of 18 recent reviews rated 1-3 are unanswered.
- booking_followup: triggered - 4 requests still say new after 2 days.
- booking_outcomes: triggered - 10 of 25 settled past visits did not happen (40%).
- performance: clear - Largest measured fall 9.5% is below the 10% reporting floor.
- search: triggered - 2 of 9 matched terms fell at least 20%, losing 1,999 impressions.
- rankings: triggered - 9 of 9 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-012 - Brightpath Dental — Chandler Ocotillo

Health `##############......` 69/100 (fair). 2 checks passed, 5 failed, 3 not evaluated (70% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | n/a | 0 | 0 | 1 | 0 |
| Local visibility | 48 | 0 | 2 | 0 | 10 |
| Operations | 45 | 0 | 1 | 1 | 1 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 75 | 0 | 1 | 1 | 1 |

Metrics:

- Impressions (28d): 2575 (+10.0% vs previous window)
- Customer actions (28d): 333 (+13.7% vs previous window)
- Actions per impression: 12.93% (+3.4% vs previous window)
- Average rating (90d): 4.25 stars
- Reviews received (90d): 4
- Reviews with a reply: 75%
- Unanswered reviews rated 1-3: 0
- Keywords tracked: 9
- Keywords in the local pack: 0%
- Average position where found: 29.7
- Settled past visits (90d): 9
- Cancelled or no-show: 55.6%
- Requests still marked new (28d): 3

### [critical] Reconcile outstanding appointment requests

Operations - score 91/100. Evidence confidence: high.

3 of 12 recent requests still say new after at least 2 days. The oldest was created 17 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 3, "recent_requests": 12, "oldest_age_days": 17, "wait_days": 2}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 33.

Check the result URL and listing relevance for “cosmetic dentist chandler” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 33}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist chandler", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Premier Family Dentistry", "rank_absolute": 33, "review_count": 161, "average_rating": 3.8, "photo_count": 100}, {"competitor_name": "Chandler Dental Care", "rank_absolute": 32, "review_count": 291, "average_rating": 4.2, "photo_count": 143}, {"competitor_name": "Chandler Cosmetic Dental", "rank_absolute": 26, "review_count": 365, "average_rating": 3.8, "photo_count": 95}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 36.

Check the result URL and listing relevance for “dental implants chandler” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 36}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants chandler", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Chandler Dental Care", "rank_absolute": 34, "review_count": 303, "average_rating": 4.2, "photo_count": 142}, {"competitor_name": "Chandler Cosmetic Dental", "rank_absolute": 37, "review_count": 389, "average_rating": 3.8, "photo_count": 95}, {"competitor_name": "Premier Family Dentistry", "rank_absolute": 41, "review_count": 137, "average_rating": 3.8, "photo_count": 101}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 23.

Check the result URL and listing relevance for “dentist chandler” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 23}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist chandler", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Premier Family Dentistry", "rank_absolute": 22, "review_count": 125, "average_rating": 3.8, "photo_count": 97}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist near chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 27.

Check the result URL and listing relevance for “dentist near chandler” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist near chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 27}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist near chandler", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Premier Family Dentistry", "rank_absolute": 23, "review_count": 125, "average_rating": 3.8, "photo_count": 98}, {"competitor_name": "Chandler Cosmetic Dental", "rank_absolute": 26, "review_count": 365, "average_rating": 3.8, "photo_count": 96}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 28.

Check the result URL and listing relevance for “emergency dentist chandler” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 28}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist chandler", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Premier Family Dentistry", "rank_absolute": 26, "review_count": 161, "average_rating": 3.8, "photo_count": 101}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 33.

Check the result URL and listing relevance for “invisalign chandler” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 33}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign chandler", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 30.

Check the result URL and listing relevance for “pediatric dentist chandler” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 30}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist chandler", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Premier Family Dentistry", "rank_absolute": 29, "review_count": 149, "average_rating": 3.8, "photo_count": 100}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 32.

Check the result URL and listing relevance for “teeth whitening chandler” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 32}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening chandler", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Chandler Dental Care", "rank_absolute": 32, "review_count": 291, "average_rating": 4.2, "photo_count": 140}, {"competitor_name": "Premier Family Dentistry", "rank_absolute": 38, "review_count": 125, "average_rating": 3.8, "photo_count": 101}, {"competitor_name": "Chandler Cosmetic Dental", "rank_absolute": 34, "review_count": 365, "average_rating": 3.8, "photo_count": 97}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “walk in dentist chandler”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 31.

Check the result URL and listing relevance for “walk in dentist chandler” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "walk in dentist chandler", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 31}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "walk in dentist chandler", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Chandler Cosmetic Dental", "rank_absolute": 25, "review_count": 389, "average_rating": 3.8, "photo_count": 96}, {"competitor_name": "Chandler Dental Care", "rank_absolute": 30, "review_count": 291, "average_rating": 4.2, "photo_count": 143}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath chandler”

Local visibility - score 68/100. Evidence confidence: medium.

“brightpath chandler” fell 85%, from 506 (2026-07) to 74 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath chandler”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath chandler", "previous": 506, "current": 74, "lost_impressions": 432, "decline_share": 0.8538, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Add missing profile imagery

Content - score 40/100. Evidence confidence: high.

The photo summary explicitly marks these images as missing: has_cover_photo.

Ask the manager for accurate, current imagery for: has_cover_photo. Review before uploading.

Limit: Counts cannot establish photo quality; no ranking uplift is inferred.

- media: Explicit false image flags. Values: `{"missing": ["has_cover_photo"]}`. 1 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 39/100. Evidence confidence: medium.

23 of 34 category attributes are unset (68%).

Review these available attributes; record true or false only after confirmation: implant_services, wheelchair_accessible_parking, wifi_available, online_appointments, appointment_required, has_restroom, accepts_debit_cards, language_assistance, transgender_safespace, gender_neutral_restroom, wheelchair_accessible_restroom, tv_in_waiting_area, walk_ins_welcome, payment_plans_available, wheelchair_accessible_entrance, has_onsite_parking, accepts_nfc_mobile_payments, sedation_available, pediatric_care, identifies_as_women_owned, evening_appointments, identifies_as_veteran_owned, mask_required.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 23, "unset_share": 0.6765, "missing": ["implant_services", "wheelchair_accessible_parking", "wifi_available", "online_appointments", "appointment_required", "has_restroom", "accepts_debit_cards", "language_assistance", "transgender_safespace", "gender_neutral_restroom", "wheelchair_accessible_restroom", "tv_in_waiting_area", "walk_ins_welcome", "payment_plans_available", "wheelchair_accessible_entrance", "has_onsite_parking", "accepts_nfc_mobile_payments", "sedation_available", "pediatric_care", "identifies_as_women_owned", "evening_appointments", "identifies_as_veteran_owned", "mask_required"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 11}`. 11 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 23 of 34 category attributes are unset.
- media: triggered - 1 profile images are explicitly marked missing.
- posts: insufficient_data - No dated posts; cannot establish feed completeness.
- reviews: insufficient_data - Too few recent valid reviews or stale activity.
- booking_followup: triggered - 3 requests still say new after 2 days.
- booking_outcomes: insufficient_data - Fewer than 20 settled past visits in 90 days (9).
- performance: clear - Largest measured fall -3.4% is below the 10% reporting floor.
- search: triggered - 1 of 3 matched terms fell at least 20%, losing 432 impressions.
- rankings: triggered - 9 of 9 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-008 - Brightpath Dental — Katy

Health `##############......` 69/100 (fair). 4 checks passed, 5 failed, 1 not evaluated (90% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 52 | 0 | 1 | 0 | 1 |
| Local visibility | 49 | 0 | 2 | 0 | 11 |
| Operations | 51 | 0 | 1 | 1 | 1 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 100 | 2 | 0 | 0 | 0 |

Metrics:

- Impressions (28d): 14727 (+2.1% vs previous window)
- Customer actions (28d): 1859 (+5.6% vs previous window)
- Actions per impression: 12.62% (+3.4% vs previous window)
- Average rating (90d): 4.43 stars
- Reviews received (90d): 23
- Reviews with a reply: 39.1%
- Unanswered reviews rated 1-3: 1
- Keywords tracked: 9
- Keywords in the local pack: 0%
- Average position where found: 13.1
- Settled past visits (90d): 14
- Cancelled or no-show: 42.9%
- Requests still marked new (28d): 3
- Days since last post: 10 days

### [critical] Reconcile outstanding appointment requests

Operations - score 92/100. Evidence confidence: high.

2 of 13 recent requests still say new after at least 2 days. The oldest was created 18 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 2, "recent_requests": 13, "oldest_age_days": 18, "wait_days": 2}`. 2 source records (IDs and full rows in JSON).

### [critical] Respond to unanswered critical reviews

Reputation - score 75/100. Evidence confidence: high.

1 reviews rated 1-3 remain unanswered after 3 days, among 8 recent reviews (12%). The oldest has waited 19 days.

Read the flagged reviews, acknowledge the concern without sharing customer details, and invite private follow-up. Investigate recurring issues internally.

Limit: Reply state is current; reviews are a self-selected sample. No automatic public reply is sent.

- reviews: Count rating <= 3, reply absent, age >= wait days. Values: `{"unanswered": 1, "pending_row_ids": ["fc1a6d04-038f-4b65-b05a-e4032bf96978"], "recent_reviews": 8, "unanswered_share": 0.125, "oldest_wait_days": 19, "wait_days": 3}`. 8 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 12.

Check the result URL and listing relevance for “cosmetic dentist katy” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 12}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist katy", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Katy Dental Center", "rank_absolute": 12, "review_count": 290, "average_rating": 3.9, "photo_count": 44}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “dental implants katy” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants katy", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Katy Dental Center", "rank_absolute": 14, "review_count": 266, "average_rating": 3.9, "photo_count": 43}, {"competitor_name": "Katy Smile Studio", "rank_absolute": 11, "review_count": 361, "average_rating": 3.9, "photo_count": 101}, {"competitor_name": "Memorial Dental Care", "rank_absolute": 12, "review_count": 376, "average_rating": 4.5, "photo_count": 46}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “dentist katy” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist katy", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Katy Smile Studio", "rank_absolute": 12, "review_count": 337, "average_rating": 3.9, "photo_count": 104}, {"competitor_name": "Katy Dental Center", "rank_absolute": 8, "review_count": 278, "average_rating": 3.9, "photo_count": 41}, {"competitor_name": "Memorial Dental Care", "rank_absolute": 8, "review_count": 376, "average_rating": 4.5, "photo_count": 43}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist near katy tx”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 11.

Check the result URL and listing relevance for “dentist near katy tx” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist near katy tx", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 11}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist near katy tx", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Katy Smile Studio", "rank_absolute": 10, "review_count": 325, "average_rating": 3.9, "photo_count": 102}, {"competitor_name": "Memorial Dental Care", "rank_absolute": 12, "review_count": 352, "average_rating": 4.5, "photo_count": 42}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “emergency dentist katy” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist katy", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Katy Dental Center", "rank_absolute": 6, "review_count": 278, "average_rating": 3.9, "photo_count": 41}, {"competitor_name": "Katy Smile Studio", "rank_absolute": 10, "review_count": 337, "average_rating": 3.9, "photo_count": 101}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “invisalign katy” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign katy", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Katy Smile Studio", "rank_absolute": 8, "review_count": 337, "average_rating": 3.9, "photo_count": 102}, {"competitor_name": "Katy Dental Center", "rank_absolute": 11, "review_count": 302, "average_rating": 3.9, "photo_count": 41}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “pediatric dentist katy” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist katy", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “teeth whitening katy” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening katy", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “walk in dentist katy”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 12.

Check the result URL and listing relevance for “walk in dentist katy” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "walk in dentist katy", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 12}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "walk in dentist katy", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Memorial Dental Care", "rank_absolute": 14, "review_count": 364, "average_rating": 4.5, "photo_count": 42}, {"competitor_name": "Katy Dental Center", "rank_absolute": 11, "review_count": 266, "average_rating": 3.9, "photo_count": 45}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “dental implants cost”

Local visibility - score 68/100. Evidence confidence: medium.

“dental implants cost” fell 60%, from 509 (2026-07) to 202 impressions (2026-08).

Inspect the listing and relevant website page for “dental implants cost”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "dental implants cost", "previous": 509, "current": 202, "lost_impressions": 307, "decline_share": 0.6031, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Lost search visibility for “emergency dentist”

Local visibility - score 43/100. Evidence confidence: medium.

“emergency dentist” fell 22%, from 2,569 (2026-07) to 2,011 impressions (2026-08).

Inspect the listing and relevant website page for “emergency dentist”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "emergency dentist", "previous": 2569, "current": 2011, "lost_impressions": 558, "decline_share": 0.2172, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 40/100. Evidence confidence: medium.

25 of 34 category attributes are unset (74%).

Review these available attributes; record true or false only after confirmation: implant_services, accepts_insurance, teeth_whitening, wheelchair_accessible_parking, wifi_available, lgbtq_friendly, online_appointments, digital_xray, has_restroom, accepts_credit_cards, language_assistance, gender_neutral_restroom, wheelchair_accessible_restroom, accepts_new_patients, walk_ins_welcome, payment_plans_available, saturday_appointments, wheelchair_accessible_entrance, accepts_nfc_mobile_payments, sedation_available, emergency_services, pediatric_care, identifies_as_women_owned, evening_appointments, kids_area.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 25, "unset_share": 0.7353, "missing": ["implant_services", "accepts_insurance", "teeth_whitening", "wheelchair_accessible_parking", "wifi_available", "lgbtq_friendly", "online_appointments", "digital_xray", "has_restroom", "accepts_credit_cards", "language_assistance", "gender_neutral_restroom", "wheelchair_accessible_restroom", "accepts_new_patients", "walk_ins_welcome", "payment_plans_available", "saturday_appointments", "wheelchair_accessible_entrance", "accepts_nfc_mobile_payments", "sedation_available", "emergency_services", "pediatric_care", "identifies_as_women_owned", "evening_appointments", "kids_area"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 9}`. 9 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 25 of 34 category attributes are unset.
- media: clear - No explicitly missing profile or cover image.
- posts: clear - A post falls within the configured recency window.
- reviews: triggered - 1 of 8 recent reviews rated 1-3 are unanswered.
- booking_followup: triggered - 2 requests still say new after 2 days.
- booking_outcomes: insufficient_data - Fewer than 20 settled past visits in 90 days (14).
- performance: clear - Largest measured fall -2.1% is below the 10% reporting floor.
- search: triggered - 2 of 7 matched terms fell at least 20%, losing 865 impressions.
- rankings: triggered - 9 of 9 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-010 - Brightpath Dental — Arcadia

Health `##############......` 71/100 (fair). 3 checks passed, 7 failed, 0 not evaluated (100% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 43 | 0 | 2 | 0 | 11 |
| Operations | 24 | 0 | 2 | 0 | 2 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 75 | 0 | 2 | 0 | 2 |

Metrics:

- Impressions (28d): 15834 (+18.8% vs previous window)
- Customer actions (28d): 2007 (+20.7% vs previous window)
- Actions per impression: 12.68% (+1.6% vs previous window)
- Average rating (90d): 4 stars
- Reviews received (90d): 34
- Reviews with a reply: 100%
- Unanswered reviews rated 1-3: 0
- Keywords tracked: 8
- Keywords in the local pack: 0%
- Average position where found: 10.1
- Settled past visits (90d): 26
- Cancelled or no-show: 46.2%
- Requests still marked new (28d): 6
- Days since last post: 51 days

### [critical] Reconcile outstanding appointment requests

Operations - score 94/100. Evidence confidence: high.

6 of 32 recent requests still say new after at least 2 days. The oldest was created 23 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 6, "recent_requests": 32, "oldest_age_days": 23, "wait_days": 2}`. 6 source records (IDs and full rows in JSON).

### [critical] Review cancellation and no-show follow-up

Operations - score 84/100. Evidence confidence: medium.

12 of 26 settled past visits were cancelled or no-show (46.2%) over 90 days, against a 20% policy threshold.

Audit the flagged past appointments and reminder process with the manager. Check cancellation reasons before deciding whether to change reminders.

Limit: Excludes future appointments and unsettled statuses; excludes unknown outcomes. The threshold is a configurable operating policy, not an industry benchmark.

- bookings: (cancelled + no_show) / settled past visits. Values: `{"failed": 12, "cancelled": 8, "no_show": 4, "settled": 26, "rate": 0.461538, "window_days": 90, "threshold": 0.2}`. 26 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist arcadia”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 6.

Check the result URL and listing relevance for “cosmetic dentist arcadia” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist arcadia", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 6}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist arcadia", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Desert Dental Care", "rank_absolute": 6, "review_count": 341, "average_rating": 4.5, "photo_count": 127}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants arcadia”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 11.

Check the result URL and listing relevance for “dental implants arcadia” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants arcadia", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 11}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants arcadia", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Phoenix Family Dentists", "rank_absolute": 6, "review_count": 391, "average_rating": 4.9, "photo_count": 106}, {"competitor_name": "Phoenix Dental Studio", "rank_absolute": 11, "review_count": 192, "average_rating": 3.9, "photo_count": 137}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist arcadia”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “dentist arcadia” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist arcadia", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist arcadia", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist near arcadia”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 8.

Check the result URL and listing relevance for “dentist near arcadia” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist near arcadia", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 8}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist near arcadia", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Smile Arizona", "rank_absolute": 6, "review_count": 336, "average_rating": 4.6, "photo_count": 93}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist phoenix”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 8.

Check the result URL and listing relevance for “emergency dentist phoenix” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist phoenix", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 8}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist phoenix", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Modern Dental Phoenix", "rank_absolute": 6, "review_count": 352, "average_rating": 3.7, "photo_count": 128}, {"competitor_name": "Smile Arizona", "rank_absolute": 15, "review_count": 372, "average_rating": 4.6, "photo_count": 94}, {"competitor_name": "Desert Dental Care", "rank_absolute": 13, "review_count": 341, "average_rating": 4.5, "photo_count": 130}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign arcadia”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 7.

Check the result URL and listing relevance for “invisalign arcadia” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign arcadia", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 7}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign arcadia", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Phoenix Dental Studio", "rank_absolute": 5, "review_count": 180, "average_rating": 3.9, "photo_count": 133}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist arcadia”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “pediatric dentist arcadia” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist arcadia", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist arcadia", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Phoenix Dental Studio", "rank_absolute": 8, "review_count": 204, "average_rating": 3.9, "photo_count": 136}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “walk in dentist arcadia”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “walk in dentist arcadia” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "walk in dentist arcadia", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "walk in dentist arcadia", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Arizona Cosmetic Dentistry", "rank_absolute": 10, "review_count": 460, "average_rating": 4.4, "photo_count": 56}, {"competitor_name": "Phoenix Dental Studio", "rank_absolute": 10, "review_count": 192, "average_rating": 3.9, "photo_count": 138}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath dental phoenix”

Local visibility - score 68/100. Evidence confidence: medium.

“brightpath dental phoenix” fell 78%, from 1,035 (2026-07) to 228 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental phoenix”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental phoenix", "previous": 1035, "current": 228, "lost_impressions": 807, "decline_share": 0.7797, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “kids dentist”

Local visibility - score 68/100. Evidence confidence: medium.

“kids dentist” fell 76%, from 3,977 (2026-07) to 971 impressions (2026-08).

Inspect the listing and relevant website page for “kids dentist”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "kids dentist", "previous": 3977, "current": 971, "lost_impressions": 3006, "decline_share": 0.7558, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “gum disease treatment arcadia”

Local visibility - score 48/100. Evidence confidence: medium.

“gum disease treatment arcadia” fell 29%, from 1,573 (2026-07) to 1,114 impressions (2026-08).

Inspect the listing and relevant website page for “gum disease treatment arcadia”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "gum disease treatment arcadia", "previous": 1573, "current": 1114, "lost_impressions": 459, "decline_share": 0.2918, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Add missing profile imagery

Content - score 40/100. Evidence confidence: high.

The photo summary explicitly marks these images as missing: has_cover_photo.

Ask the manager for accurate, current imagery for: has_cover_photo. Review before uploading.

Limit: Counts cannot establish photo quality; no ranking uplift is inferred.

- media: Explicit false image flags. Values: `{"missing": ["has_cover_photo"]}`. 1 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 30/100. Evidence confidence: medium.

9 of 34 category attributes are unset (26%).

Review these available attributes; record true or false only after confirmation: implant_services, wheelchair_accessible_parking, has_restroom, accepts_debit_cards, walk_ins_welcome, payment_plans_available, emergency_services, identifies_as_women_owned, kids_area.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 9, "unset_share": 0.2647, "missing": ["implant_services", "wheelchair_accessible_parking", "has_restroom", "accepts_debit_cards", "walk_ins_welcome", "payment_plans_available", "emergency_services", "identifies_as_women_owned", "kids_area"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 25}`. 25 source records (IDs and full rows in JSON).

### [notice] Check whether a useful customer update is overdue

Content - score 28/100. Evidence confidence: medium.

The last recorded post was 51 days before the analysis date, past the 45-day policy window.

Confirm the post history is current; publish an accurate update only if there is useful news, a real event or an available offer.

Limit: An incomplete export can explain the gap. Posting cadence is not a rank factor established by this dataset.

- posts: as_of minus latest published_on. Values: `{"gap_days": 51, "threshold_days": 45}`. 1 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 9 of 34 category attributes are unset.
- media: triggered - 1 profile images are explicitly marked missing.
- posts: triggered - Last recorded post was 51 days ago.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: triggered - 6 requests still say new after 2 days.
- booking_outcomes: triggered - 12 of 26 settled past visits did not happen (46%).
- performance: clear - Largest measured fall -1.6% is below the 10% reporting floor.
- search: triggered - 3 of 4 matched terms fell at least 20%, losing 4,272 impressions.
- rankings: triggered - 8 of 8 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-009 - Brightpath Dental — Sugar Land

Health `##############......` 71/100 (fair). 4 checks passed, 4 failed, 2 not evaluated (80% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 19 | 0 | 2 | 0 | 2 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 48 | 0 | 2 | 0 | 12 |
| Operations | 100 | 1 | 0 | 1 | 0 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 100 | 1 | 0 | 1 | 0 |

Metrics:

- Impressions (28d): 3569 (-1.7% vs previous window)
- Customer actions (28d): 442 (-2.6% vs previous window)
- Actions per impression: 12.38% (-1.0% vs previous window)
- Average rating (90d): 4.54 stars
- Reviews received (90d): 13
- Reviews with a reply: 38.5%
- Unanswered reviews rated 1-3: 1
- Keywords tracked: 9
- Keywords in the local pack: 0%
- Average position where found: 41
- Settled past visits (90d): 2
- Cancelled or no-show: 0%
- Requests still marked new (28d): 0

### [critical] Confirm and complete customer-facing information

Profile completeness - score 80/100. Evidence confidence: high.

1 essential profile fields need confirmation, including has_voice_of_merchant.

Check the missing fields with the location manager, then update only confirmed information: has_voice_of_merchant.

Limit: This is current stored profile state; no historical reconstruction. No claim that completing fields improves rank.

- locations: Missing or unverified fields in current profile. Values: `{"missing_fields": ["has_voice_of_merchant"], "urgent_fields": ["has_voice_of_merchant"]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 37.

Check the result URL and listing relevance for “cosmetic dentist sugar land” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 37}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist sugar land", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 41.

Check the result URL and listing relevance for “dental implants sugar land” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 41}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants sugar land", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Fort Bend Dentistry", "rank_absolute": 40, "review_count": 300, "average_rating": 4.1, "photo_count": 134}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist near sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 37.

Check the result URL and listing relevance for “dentist near sugar land” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist near sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 37}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist near sugar land", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Sugar Land Dental", "rank_absolute": 32, "review_count": 397, "average_rating": 4.8, "photo_count": 116}, {"competitor_name": "Fort Bend Dentistry", "rank_absolute": 37, "review_count": 312, "average_rating": 4.1, "photo_count": 134}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 33.

Check the result URL and listing relevance for “dentist sugar land” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 33}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist sugar land", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 39.

Check the result URL and listing relevance for “emergency dentist sugar land” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 39}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist sugar land", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Sugar Land Dental", "rank_absolute": 36, "review_count": 397, "average_rating": 4.8, "photo_count": 114}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 43.

Check the result URL and listing relevance for “invisalign sugar land” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 43}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign sugar land", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Fort Bend Dentistry", "rank_absolute": 40, "review_count": 300, "average_rating": 4.1, "photo_count": 136}, {"competitor_name": "Imperial Dental Care", "rank_absolute": 41, "review_count": 378, "average_rating": 4.1, "photo_count": 116}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “orthodontist sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 43.

Check the result URL and listing relevance for “orthodontist sugar land” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "orthodontist sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 43}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "orthodontist sugar land", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 39.

Check the result URL and listing relevance for “pediatric dentist sugar land” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 39}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist sugar land", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Fort Bend Dentistry", "rank_absolute": 36, "review_count": 336, "average_rating": 4.1, "photo_count": 134}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening sugar land”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 45.

Check the result URL and listing relevance for “teeth whitening sugar land” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening sugar land", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 45}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening sugar land", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Imperial Dental Care", "rank_absolute": 45, "review_count": 366, "average_rating": 4.1, "photo_count": 118}, {"competitor_name": "Fort Bend Dentistry", "rank_absolute": 45, "review_count": 324, "average_rating": 4.1, "photo_count": 139}, {"competitor_name": "Sugar Land Dental", "rank_absolute": 42, "review_count": 385, "average_rating": 4.8, "photo_count": 113}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath dental sugar land”

Local visibility - score 68/100. Evidence confidence: medium.

“brightpath dental sugar land” fell 69%, from 259 (2026-07) to 79 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental sugar land”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental sugar land", "previous": 259, "current": 79, "lost_impressions": 180, "decline_share": 0.695, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “emergency dentist”

Local visibility - score 68/100. Evidence confidence: medium.

“emergency dentist” fell 72%, from 617 (2026-07) to 172 impressions (2026-08).

Inspect the listing and relevant website page for “emergency dentist”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "emergency dentist", "previous": 617, "current": 172, "lost_impressions": 445, "decline_share": 0.7212, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “invisalign near me”

Local visibility - score 68/100. Evidence confidence: medium.

“invisalign near me” fell 66%, from 219 (2026-07) to 74 impressions (2026-08).

Inspect the listing and relevant website page for “invisalign near me”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "invisalign near me", "previous": 219, "current": 74, "lost_impressions": 145, "decline_share": 0.6621, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 36/100. Evidence confidence: medium.

19 of 34 category attributes are unset (56%).

Review these available attributes; record true or false only after confirmation: implant_services, wifi_available, lgbtq_friendly, digital_xray, appointment_required, has_restroom, orthodontic_care, accepts_credit_cards, accepts_debit_cards, language_assistance, tv_in_waiting_area, walk_ins_welcome, payment_plans_available, saturday_appointments, wheelchair_accessible_entrance, has_onsite_parking, sedation_available, emergency_services, identifies_as_women_owned.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 19, "unset_share": 0.5588, "missing": ["implant_services", "wifi_available", "lgbtq_friendly", "digital_xray", "appointment_required", "has_restroom", "orthodontic_care", "accepts_credit_cards", "accepts_debit_cards", "language_assistance", "tv_in_waiting_area", "walk_ins_welcome", "payment_plans_available", "saturday_appointments", "wheelchair_accessible_entrance", "has_onsite_parking", "sedation_available", "emergency_services", "identifies_as_women_owned"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 15}`. 15 source records (IDs and full rows in JSON).

Coverage:

- profile: triggered - 1 essential fields need confirmation.
- attributes: triggered - 19 of 34 category attributes are unset.
- media: clear - No explicitly missing profile or cover image.
- posts: insufficient_data - No dated posts; cannot establish feed completeness.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: clear - No aged new requests in the recent window.
- booking_outcomes: insufficient_data - Fewer than 20 settled past visits in 90 days (2).
- performance: clear - Largest measured fall 1.7% is below the 10% reporting floor.
- search: triggered - 3 of 9 matched terms fell at least 20%, losing 770 impressions.
- rankings: triggered - 9 of 9 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-011 - Brightpath Dental — Tempe Marketplace

Health `##############......` 72/100 (fair). 4 checks passed, 6 failed, 0 not evaluated (100% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 40 | 0 | 2 | 0 | 18 |
| Operations | 26 | 0 | 2 | 0 | 2 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 88 | 1 | 1 | 0 | 1 |

Metrics:

- Impressions (28d): 13780 (+0.5% vs previous window)
- Customer actions (28d): 1702 (+0.5% vs previous window)
- Actions per impression: 12.35% (+0.0% vs previous window)
- Average rating (90d): 2.75 stars
- Reviews received (90d): 44
- Reviews with a reply: 20.5%
- Unanswered reviews rated 1-3: 24
- Keywords tracked: 11
- Keywords in the local pack: 0%
- Average position where found: 10
- Settled past visits (90d): 21
- Cancelled or no-show: 42.9%
- Requests still marked new (28d): 5
- Days since last post: 30 days

### [critical] Reconcile outstanding appointment requests

Operations - score 88/100. Evidence confidence: high.

5 of 38 recent requests still say new after at least 2 days. The oldest was created 14 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 5, "recent_requests": 38, "oldest_age_days": 14, "wait_days": 2}`. 5 source records (IDs and full rows in JSON).

### [critical] Review cancellation and no-show follow-up

Operations - score 81/100. Evidence confidence: medium.

9 of 21 settled past visits were cancelled or no-show (42.9%) over 90 days, against a 20% policy threshold.

Audit the flagged past appointments and reminder process with the manager. Check cancellation reasons before deciding whether to change reminders.

Limit: Excludes future appointments and unsettled statuses; excludes unknown outcomes. The threshold is a configurable operating policy, not an industry benchmark.

- bookings: (cancelled + no_show) / settled past visits. Values: `{"failed": 9, "cancelled": 6, "no_show": 3, "settled": 21, "rate": 0.428571, "window_days": 90, "threshold": 0.2}`. 21 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “cosmetic dentist tempe” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist tempe", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "ASU Dental Partners", "rank_absolute": 8, "review_count": 411, "average_rating": 3.7, "photo_count": 101}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 11.

Check the result URL and listing relevance for “dental implants tempe” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 11}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants tempe", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist near tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 8.

Check the result URL and listing relevance for “dentist near tempe” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist near tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 8}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist near tempe", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 8.

Check the result URL and listing relevance for “dentist tempe” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 8}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist tempe", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "ASU Dental Partners", "rank_absolute": 3, "review_count": 375, "average_rating": 3.7, "photo_count": 98}, {"competitor_name": "Arizona Smile Dental", "rank_absolute": 6, "review_count": 218, "average_rating": 3.9, "photo_count": 119}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dental care tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “emergency dental care tempe” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dental care tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dental care tempe", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Arizona Smile Dental", "rank_absolute": 10, "review_count": 230, "average_rating": 3.9, "photo_count": 122}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 6.

Check the result URL and listing relevance for “emergency dentist tempe” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 6}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist tempe", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist tempe az”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 8.

Check the result URL and listing relevance for “emergency dentist tempe az” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist tempe az", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 8}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist tempe az", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Arizona Smile Dental", "rank_absolute": 7, "review_count": 218, "average_rating": 3.9, "photo_count": 118}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 7.

Check the result URL and listing relevance for “invisalign tempe” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 7}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign tempe", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “orthodontist tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 6.

Check the result URL and listing relevance for “orthodontist tempe” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "orthodontist tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 6}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "orthodontist tempe", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “pediatric dentist tempe” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist tempe", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “walk in dentist tempe”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “walk in dentist tempe” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "walk in dentist tempe", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "walk in dentist tempe", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "ASU Dental Partners", "rank_absolute": 6, "review_count": 411, "average_rating": 3.7, "photo_count": 97}, {"competitor_name": "Tempe Dental Associates", "rank_absolute": 9, "review_count": 275, "average_rating": 4.1, "photo_count": 140}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath dental”

Local visibility - score 68/100. Evidence confidence: medium.

“brightpath dental” fell 67%, from 415 (2026-07) to 138 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental", "previous": 415, "current": 138, "lost_impressions": 277, "decline_share": 0.6675, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath dental tempe”

Local visibility - score 68/100. Evidence confidence: medium.

“brightpath dental tempe” fell 62%, from 1,411 (2026-07) to 530 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental tempe”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental tempe", "previous": 1411, "current": 530, "lost_impressions": 881, "decline_share": 0.6244, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “pediatric dentist near me”

Local visibility - score 68/100. Evidence confidence: medium.

“pediatric dentist near me” fell 89%, from 1,587 (2026-07) to 175 impressions (2026-08).

Inspect the listing and relevant website page for “pediatric dentist near me”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "pediatric dentist near me", "previous": 1587, "current": 175, "lost_impressions": 1412, "decline_share": 0.8897, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “kids dentist”

Local visibility - score 52/100. Evidence confidence: medium.

“kids dentist” fell 36%, from 384 (2026-07) to 247 impressions (2026-08).

Inspect the listing and relevant website page for “kids dentist”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "kids dentist", "previous": 384, "current": 247, "lost_impressions": 137, "decline_share": 0.3568, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “teeth cleaning near me”

Local visibility - score 51/100. Evidence confidence: medium.

“teeth cleaning near me” fell 34%, from 3,338 (2026-07) to 2,218 impressions (2026-08).

Inspect the listing and relevant website page for “teeth cleaning near me”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "teeth cleaning near me", "previous": 3338, "current": 2218, "lost_impressions": 1120, "decline_share": 0.3355, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “cavity filling”

Local visibility - score 50/100. Evidence confidence: medium.

“cavity filling” fell 32%, from 786 (2026-07) to 531 impressions (2026-08).

Inspect the listing and relevant website page for “cavity filling”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "cavity filling", "previous": 786, "current": 531, "lost_impressions": 255, "decline_share": 0.3244, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath dental phoenix”

Local visibility - score 45/100. Evidence confidence: medium.

“brightpath dental phoenix” fell 25%, from 550 (2026-07) to 412 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental phoenix”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental phoenix", "previous": 550, "current": 412, "lost_impressions": 138, "decline_share": 0.2509, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Add missing profile imagery

Content - score 40/100. Evidence confidence: high.

The photo summary explicitly marks these images as missing: has_cover_photo.

Ask the manager for accurate, current imagery for: has_cover_photo. Review before uploading.

Limit: Counts cannot establish photo quality; no ranking uplift is inferred.

- media: Explicit false image flags. Values: `{"missing": ["has_cover_photo"]}`. 1 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 30/100. Evidence confidence: medium.

8 of 34 category attributes are unset (24%).

Review these available attributes; record true or false only after confirmation: online_appointments, appointment_required, has_restroom, language_assistance, wheelchair_accessible_restroom, wheelchair_accessible_entrance, pediatric_care, identifies_as_veteran_owned.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 8, "unset_share": 0.2353, "missing": ["online_appointments", "appointment_required", "has_restroom", "language_assistance", "wheelchair_accessible_restroom", "wheelchair_accessible_entrance", "pediatric_care", "identifies_as_veteran_owned"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 26}`. 26 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 8 of 34 category attributes are unset.
- media: triggered - 1 profile images are explicitly marked missing.
- posts: clear - A post falls within the configured recency window.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: triggered - 5 requests still say new after 2 days.
- booking_outcomes: triggered - 9 of 21 settled past visits did not happen (43%).
- performance: clear - Largest measured fall -0.0% is below the 10% reporting floor.
- search: triggered - 7 of 7 matched terms fell at least 20%, losing 4,220 impressions.
- rankings: triggered - 11 of 11 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-007 - Brightpath Dental — Montrose

Health `###############.....` 73/100 (fair). 4 checks passed, 6 failed, 0 not evaluated (100% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 46 | 0 | 2 | 0 | 11 |
| Operations | 25 | 0 | 2 | 0 | 2 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 88 | 1 | 1 | 0 | 1 |

Metrics:

- Impressions (28d): 12293 (-0.9% vs previous window)
- Customer actions (28d): 1543 (+0.1% vs previous window)
- Actions per impression: 12.55% (+1.0% vs previous window)
- Average rating (90d): 4.37 stars
- Reviews received (90d): 35
- Reviews with a reply: 51.4%
- Unanswered reviews rated 1-3: 3
- Keywords tracked: 9
- Keywords in the local pack: 0%
- Average position where found: 13
- Settled past visits (90d): 33
- Cancelled or no-show: 42.4%
- Requests still marked new (28d): 6
- Days since last post: 20 days

### [critical] Reconcile outstanding appointment requests

Operations - score 94/100. Evidence confidence: high.

5 of 33 recent requests still say new after at least 2 days. The oldest was created 22 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 5, "recent_requests": 33, "oldest_age_days": 22, "wait_days": 2}`. 5 source records (IDs and full rows in JSON).

### [critical] Review cancellation and no-show follow-up

Operations - score 80/100. Evidence confidence: medium.

14 of 33 settled past visits were cancelled or no-show (42.4%) over 90 days, against a 20% policy threshold.

Audit the flagged past appointments and reminder process with the manager. Check cancellation reasons before deciding whether to change reminders.

Limit: Excludes future appointments and unsettled statuses; excludes unknown outcomes. The threshold is a configurable operating policy, not an industry benchmark.

- bookings: (cancelled + no_show) / settled past visits. Values: `{"failed": 14, "cancelled": 11, "no_show": 3, "settled": 33, "rate": 0.424242, "window_days": 90, "threshold": 0.2}`. 33 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist houston”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “cosmetic dentist houston” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist houston", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist houston", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Texas Dental Associates", "rank_absolute": 9, "review_count": 260, "average_rating": 4.2, "photo_count": 48}, {"competitor_name": "Houston Emergency Dental", "rank_absolute": 9, "review_count": 430, "average_rating": 3.8, "photo_count": 31}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants houston”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 14.

Check the result URL and listing relevance for “dental implants houston” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants houston", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 14}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants houston", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Coastal Smile Dentistry", "rank_absolute": 11, "review_count": 193, "average_rating": 4.6, "photo_count": 35}, {"competitor_name": "Texas Dental Associates", "rank_absolute": 14, "review_count": 236, "average_rating": 4.2, "photo_count": 45}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist houston montrose”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “dentist houston montrose” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist houston montrose", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist houston montrose", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Houston Emergency Dental", "rank_absolute": 11, "review_count": 406, "average_rating": 3.8, "photo_count": 28}, {"competitor_name": "Texas Dental Associates", "rank_absolute": 9, "review_count": 272, "average_rating": 4.2, "photo_count": 46}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist montrose”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “dentist montrose” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist montrose", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist montrose", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Vista Point Dental", "rank_absolute": 12, "review_count": 275, "average_rating": 4.2, "photo_count": 98}, {"competitor_name": "Family Care Houston", "rank_absolute": 12, "review_count": 223, "average_rating": 4.4, "photo_count": 76}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist near montrose”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 15.

Check the result URL and listing relevance for “dentist near montrose” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist near montrose", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 15}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist near montrose", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist houston”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “emergency dentist houston” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist houston", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist houston", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign houston”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “invisalign houston” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign houston", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign houston", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Vista Point Dental", "rank_absolute": 8, "review_count": 275, "average_rating": 4.2, "photo_count": 99}, {"competitor_name": "Family Care Houston", "rank_absolute": 10, "review_count": 247, "average_rating": 4.4, "photo_count": 76}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist houston”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 12.

Check the result URL and listing relevance for “pediatric dentist houston” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist houston", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 12}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist houston", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Houston Emergency Dental", "rank_absolute": 11, "review_count": 442, "average_rating": 3.8, "photo_count": 30}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening montrose”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “teeth whitening montrose” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening montrose", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening montrose", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Houston Emergency Dental", "rank_absolute": 9, "review_count": 442, "average_rating": 3.8, "photo_count": 29}, {"competitor_name": "Houston Dental Group", "rank_absolute": 9, "review_count": 441, "average_rating": 4.5, "photo_count": 135}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “best dentist near me”

Local visibility - score 68/100. Evidence confidence: medium.

“best dentist near me” fell 94%, from 1,468 (2026-07) to 83 impressions (2026-08).

Inspect the listing and relevant website page for “best dentist near me”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "best dentist near me", "previous": 1468, "current": 83, "lost_impressions": 1385, "decline_share": 0.9435, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “dental implants”

Local visibility - score 45/100. Evidence confidence: medium.

“dental implants” fell 25%, from 629 (2026-07) to 472 impressions (2026-08).

Inspect the listing and relevant website page for “dental implants”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "dental implants", "previous": 629, "current": 472, "lost_impressions": 157, "decline_share": 0.2496, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Add missing profile imagery

Content - score 40/100. Evidence confidence: high.

The photo summary explicitly marks these images as missing: has_cover_photo.

Ask the manager for accurate, current imagery for: has_cover_photo. Review before uploading.

Limit: Counts cannot establish photo quality; no ranking uplift is inferred.

- media: Explicit false image flags. Values: `{"missing": ["has_cover_photo"]}`. 1 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 33/100. Evidence confidence: medium.

14 of 34 category attributes are unset (41%).

Review these available attributes; record true or false only after confirmation: teeth_whitening, wifi_available, lgbtq_friendly, orthodontic_care, accepts_credit_cards, wheelchair_accessible_restroom, tv_in_waiting_area, saturday_appointments, sedation_available, emergency_services, pediatric_care, identifies_as_women_owned, evening_appointments, kids_area.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 14, "unset_share": 0.4118, "missing": ["teeth_whitening", "wifi_available", "lgbtq_friendly", "orthodontic_care", "accepts_credit_cards", "wheelchair_accessible_restroom", "tv_in_waiting_area", "saturday_appointments", "sedation_available", "emergency_services", "pediatric_care", "identifies_as_women_owned", "evening_appointments", "kids_area"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 20}`. 20 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 14 of 34 category attributes are unset.
- media: triggered - 1 profile images are explicitly marked missing.
- posts: clear - A post falls within the configured recency window.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: triggered - 5 requests still say new after 2 days.
- booking_outcomes: triggered - 14 of 33 settled past visits did not happen (42%).
- performance: clear - Largest measured fall 0.9% is below the 10% reporting floor.
- search: triggered - 2 of 4 matched terms fell at least 20%, losing 1,542 impressions.
- rankings: triggered - 9 of 9 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-001 - Brightpath Dental — Mueller

Health `###############.....` 75/100 (good). 5 checks passed, 5 failed, 0 not evaluated (100% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 50 | 0 | 2 | 0 | 11 |
| Operations | 27 | 0 | 2 | 0 | 2 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 100 | 2 | 0 | 0 | 0 |

Metrics:

- Impressions (28d): 25600 (-1.7% vs previous window)
- Customer actions (28d): 3172 (-0.0% vs previous window)
- Actions per impression: 12.39% (+1.6% vs previous window)
- Average rating (90d): 4.03 stars
- Reviews received (90d): 59
- Reviews with a reply: 79.7%
- Unanswered reviews rated 1-3: 2
- Keywords tracked: 10
- Keywords in the local pack: 0%
- Average position where found: 9.3
- Settled past visits (90d): 46
- Cancelled or no-show: 39.1%
- Requests still marked new (28d): 4
- Days since last post: 9 days

### [critical] Reconcile outstanding appointment requests

Operations - score 94/100. Evidence confidence: high.

4 of 38 recent requests still say new after at least 2 days. The oldest was created 24 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 4, "recent_requests": 38, "oldest_age_days": 24, "wait_days": 2}`. 4 source records (IDs and full rows in JSON).

### [critical] Review cancellation and no-show follow-up

Operations - score 77/100. Evidence confidence: medium.

18 of 46 settled past visits were cancelled or no-show (39.1%) over 90 days, against a 20% policy threshold.

Audit the flagged past appointments and reminder process with the manager. Check cancellation reasons before deciding whether to change reminders.

Limit: Excludes future appointments and unsettled statuses; excludes unknown outcomes. The threshold is a configurable operating policy, not an industry benchmark.

- bookings: (cancelled + no_show) / settled past visits. Values: `{"failed": 18, "cancelled": 13, "no_show": 5, "settled": 46, "rate": 0.391304, "window_days": 90, "threshold": 0.2}`. 46 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 6.

Check the result URL and listing relevance for “cosmetic dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 6}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 6.

Check the result URL and listing relevance for “dental implants austin” on desktop. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 6}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants austin", "device": "desktop"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Cedar Ridge Dental Care", "rank_absolute": 7, "review_count": 336, "average_rating": 4.8, "photo_count": 94}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental insurance accepted austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “dental insurance accepted austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental insurance accepted austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental insurance accepted austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Cedar Ridge Dental Care", "rank_absolute": 11, "review_count": 324, "average_rating": 4.8, "photo_count": 96}, {"competitor_name": "Downtown Dental Associates", "rank_absolute": 9, "review_count": 235, "average_rating": 4.2, "photo_count": 75}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Austin Smile Dental", "rank_absolute": 11, "review_count": 163, "average_rating": 3.7, "photo_count": 93}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist open saturday austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 12.

Check the result URL and listing relevance for “dentist open saturday austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist open saturday austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 12}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist open saturday austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Advanced Cosmetic Dentistry", "rank_absolute": 7, "review_count": 147, "average_rating": 4.0, "photo_count": 58}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 4.

Check the result URL and listing relevance for “emergency dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 4}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Downtown Dental Associates", "rank_absolute": 1, "review_count": 199, "average_rating": 4.2, "photo_count": 74}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 4.

Check the result URL and listing relevance for “invisalign austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 4}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 10.

Check the result URL and listing relevance for “pediatric dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 10}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Lakeview Family Dentistry", "rank_absolute": 6, "review_count": 157, "average_rating": 3.8, "photo_count": 139}, {"competitor_name": "Downtown Dental Associates", "rank_absolute": 12, "review_count": 199, "average_rating": 4.2, "photo_count": 76}, {"competitor_name": "Cedar Ridge Dental Care", "rank_absolute": 6, "review_count": 360, "average_rating": 4.8, "photo_count": 93}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 6.

Check the result URL and listing relevance for “teeth whitening austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 6}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “walk in dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 9.

Check the result URL and listing relevance for “walk in dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "walk in dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 9}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "walk in dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Cedar Ridge Dental Care", "rank_absolute": 10, "review_count": 348, "average_rating": 4.8, "photo_count": 95}, {"competitor_name": "Downtown Dental Associates", "rank_absolute": 9, "review_count": 235, "average_rating": 4.2, "photo_count": 75}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “dentist with payment plans”

Local visibility - score 68/100. Evidence confidence: medium.

“dentist with payment plans” fell 89%, from 1,529 (2026-07) to 164 impressions (2026-08).

Inspect the listing and relevant website page for “dentist with payment plans”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "dentist with payment plans", "previous": 1529, "current": 164, "lost_impressions": 1365, "decline_share": 0.8927, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 27/100. Evidence confidence: medium.

4 of 34 category attributes are unset (12%).

Review these available attributes; record true or false only after confirmation: lgbtq_friendly, appointment_required, payment_plans_available, emergency_services.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 4, "unset_share": 0.1176, "missing": ["lgbtq_friendly", "appointment_required", "payment_plans_available", "emergency_services"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 30}`. 30 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 4 of 34 category attributes are unset.
- media: clear - No explicitly missing profile or cover image.
- posts: clear - A post falls within the configured recency window.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: triggered - 4 requests still say new after 2 days.
- booking_outcomes: triggered - 18 of 46 settled past visits did not happen (39%).
- performance: clear - Largest measured fall 1.7% is below the 10% reporting floor.
- search: triggered - 1 of 6 matched terms fell at least 20%, losing 1,365 impressions.
- rankings: triggered - 10 of 10 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-002 - Brightpath Dental — South Lamar

Health `###############.....` 77/100 (good). 3 checks passed, 5 failed, 2 not evaluated (80% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 50 | 0 | 2 | 0 | 9 |
| Operations | 57 | 0 | 1 | 1 | 1 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 75 | 0 | 1 | 1 | 1 |

Metrics:

- Impressions (28d): 12328 (+0.4% vs previous window)
- Customer actions (28d): 803 (-0.9% vs previous window)
- Actions per impression: 6.51% (-1.2% vs previous window)
- Average rating (90d): 4.48 stars
- Reviews received (90d): 33
- Reviews with a reply: 60.6%
- Unanswered reviews rated 1-3: 0
- Keywords tracked: 8
- Keywords in the local pack: 0%
- Average position where found: 15
- Settled past visits (90d): 16
- Cancelled or no-show: 50%
- Requests still marked new (28d): 1

### [critical] Reconcile outstanding appointment requests

Operations - score 81/100. Evidence confidence: high.

1 of 24 recent requests still say new after at least 2 days. The oldest was created 7 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 1, "recent_requests": 24, "oldest_age_days": 7, "wait_days": 2}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “cosmetic dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 14.

Check the result URL and listing relevance for “cosmetic dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "cosmetic dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 14}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "cosmetic dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Lakeview Family Dentistry", "rank_absolute": 11, "review_count": 157, "average_rating": 3.8, "photo_count": 139}, {"competitor_name": "Austin Smile Dental", "rank_absolute": 14, "review_count": 187, "average_rating": 3.7, "photo_count": 93}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 12.

Check the result URL and listing relevance for “dental implants austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 12}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Lakeview Family Dentistry", "rank_absolute": 12, "review_count": 193, "average_rating": 3.8, "photo_count": 139}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 3, "rivals": [{"competitor_name": "Austin Smile Dental", "rank_absolute": 12, "review_count": 163, "average_rating": 3.7, "photo_count": 91}, {"competitor_name": "Lakeview Family Dentistry", "rank_absolute": 16, "review_count": 181, "average_rating": 3.8, "photo_count": 138}, {"competitor_name": "Downtown Dental Associates", "rank_absolute": 16, "review_count": 211, "average_rating": 4.2, "photo_count": 77}]}`. 3 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dentist open saturday austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 18.

Check the result URL and listing relevance for “dentist open saturday austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dentist open saturday austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 18}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dentist open saturday austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Cedar Ridge Dental Care", "rank_absolute": 14, "review_count": 348, "average_rating": 4.8, "photo_count": 93}, {"competitor_name": "Lakeview Family Dentistry", "rank_absolute": 17, "review_count": 193, "average_rating": 3.8, "photo_count": 139}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 12.

Check the result URL and listing relevance for “emergency dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 12}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 2, "rivals": [{"competitor_name": "Lakeview Family Dentistry", "rank_absolute": 7, "review_count": 181, "average_rating": 3.8, "photo_count": 137}, {"competitor_name": "Austin Smile Dental", "rank_absolute": 10, "review_count": 175, "average_rating": 3.7, "photo_count": 93}]}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “invisalign austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 13.

Check the result URL and listing relevance for “invisalign austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "invisalign austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 13}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "invisalign austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Austin Smile Dental", "rank_absolute": 13, "review_count": 187, "average_rating": 3.7, "photo_count": 95}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “pediatric dentist austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 14.

Check the result URL and listing relevance for “pediatric dentist austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "pediatric dentist austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 14}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "pediatric dentist austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening austin”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 11.

Check the result URL and listing relevance for “teeth whitening austin” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening austin", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 11}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening austin", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Advanced Cosmetic Dentistry", "rank_absolute": 10, "review_count": 135, "average_rating": 4.0, "photo_count": 55}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “dentist open sunday”

Local visibility - score 49/100. Evidence confidence: medium.

“dentist open sunday” fell 30%, from 773 (2026-07) to 538 impressions (2026-08).

Inspect the listing and relevant website page for “dentist open sunday”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "dentist open sunday", "previous": 773, "current": 538, "lost_impressions": 235, "decline_share": 0.304, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Add missing profile imagery

Content - score 40/100. Evidence confidence: high.

The photo summary explicitly marks these images as missing: has_cover_photo.

Ask the manager for accurate, current imagery for: has_cover_photo. Review before uploading.

Limit: Counts cannot establish photo quality; no ranking uplift is inferred.

- media: Explicit false image flags. Values: `{"missing": ["has_cover_photo"]}`. 1 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 32/100. Evidence confidence: medium.

12 of 34 category attributes are unset (35%).

Review these available attributes; record true or false only after confirmation: implant_services, accepts_insurance, digital_xray, orthodontic_care, accepts_credit_cards, accepts_debit_cards, transgender_safespace, gender_neutral_restroom, wheelchair_accessible_restroom, wheelchair_accessible_entrance, has_onsite_parking, kids_area.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 12, "unset_share": 0.3529, "missing": ["implant_services", "accepts_insurance", "digital_xray", "orthodontic_care", "accepts_credit_cards", "accepts_debit_cards", "transgender_safespace", "gender_neutral_restroom", "wheelchair_accessible_restroom", "wheelchair_accessible_entrance", "has_onsite_parking", "kids_area"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 22}`. 22 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 12 of 34 category attributes are unset.
- media: triggered - 1 profile images are explicitly marked missing.
- posts: insufficient_data - No dated posts; cannot establish feed completeness.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: triggered - 1 requests still say new after 2 days.
- booking_outcomes: insufficient_data - Fewer than 20 settled past visits in 90 days (16).
- performance: clear - Largest measured fall 1.2% is below the 10% reporting floor.
- search: triggered - 1 of 6 matched terms fell at least 20%, losing 235 impressions.
- rankings: triggered - 8 of 8 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.

## LOC-005 - Brightpath Dental — Plano Legacy

Health `################....` 78/100 (good). 5 checks passed, 5 failed, 0 not evaluated (100% coverage).

| Category | Score | Passed | Failed | Not evaluated | Issues |
| --- | --- | --- | --- | --- | --- |
| Profile completeness | 94 | 1 | 1 | 0 | 1 |
| Reputation | 100 | 1 | 0 | 0 | 0 |
| Local visibility | 61 | 0 | 2 | 0 | 10 |
| Operations | 26 | 0 | 2 | 0 | 2 |
| Performance | 100 | 1 | 0 | 0 | 0 |
| Content | 100 | 2 | 0 | 0 | 0 |

Metrics:

- Impressions (28d): 27877 (-0.4% vs previous window)
- Customer actions (28d): 3539 (+2.1% vs previous window)
- Actions per impression: 12.7% (+2.5% vs previous window)
- Average rating (90d): 4.18 stars
- Reviews received (90d): 62
- Reviews with a reply: 100%
- Unanswered reviews rated 1-3: 0
- Keywords tracked: 12
- Keywords in the local pack: 41.7%
- Average position where found: 3.3
- Settled past visits (90d): 37
- Cancelled or no-show: 45.9%
- Requests still marked new (28d): 5
- Days since last post: 4 days

### [critical] Reconcile outstanding appointment requests

Operations - score 94/100. Evidence confidence: high.

5 of 38 recent requests still say new after at least 2 days. The oldest was created 27 days ago.

Check the flagged requests in the booking system. Confirm pending appointments or correct stale statuses before contacting customers.

Limit: Current statuses may be stale. This is a reconciliation task, not proof of lost appointments.

- bookings: Count new requests aged >= configured wait. Values: `{"count": 5, "recent_requests": 38, "oldest_age_days": 27, "wait_days": 2}`. 5 source records (IDs and full rows in JSON).

### [critical] Review cancellation and no-show follow-up

Operations - score 84/100. Evidence confidence: medium.

17 of 37 settled past visits were cancelled or no-show (45.9%) over 90 days, against a 20% policy threshold.

Audit the flagged past appointments and reminder process with the manager. Check cancellation reasons before deciding whether to change reminders.

Limit: Excludes future appointments and unsettled statuses; excludes unknown outcomes. The threshold is a configurable operating policy, not an industry benchmark.

- bookings: (cancelled + no_show) / settled past visits. Values: `{"failed": 17, "cancelled": 13, "no_show": 4, "settled": 37, "rate": 0.459459, "window_days": 90, "threshold": 0.2}`. 37 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “walk in dentist plano”

Local visibility - score 72/100. Evidence confidence: medium.

This keyword missed the local pack in 4 of 4 consecutive checks, best observed position 5.

Check the result URL and listing relevance for “walk in dentist plano” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "walk in dentist plano", "outside_pack": 4, "weeks": 4, "never_found": false, "best_absolute_rank": 5}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "walk in dentist plano", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Premier Dental Care", "rank_absolute": 3, "review_count": 254, "average_rating": 3.9, "photo_count": 30}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “dental implants”

Local visibility - score 68/100. Evidence confidence: medium.

“dental implants” fell 87%, from 889 (2026-07) to 112 impressions (2026-08).

Inspect the listing and relevant website page for “dental implants”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "dental implants", "previous": 889, "current": 112, "lost_impressions": 777, "decline_share": 0.874, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “gum disease treatment”

Local visibility - score 68/100. Evidence confidence: medium.

“gum disease treatment” fell 81%, from 1,745 (2026-07) to 323 impressions (2026-08).

Inspect the listing and relevant website page for “gum disease treatment”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "gum disease treatment", "previous": 1745, "current": 323, "lost_impressions": 1422, "decline_share": 0.8149, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “dental implants plano”

Local visibility - score 61/100. Evidence confidence: medium.

This keyword missed the local pack in 3 of 4 consecutive checks, best observed position 3.

Check the result URL and listing relevance for “dental implants plano” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "dental implants plano", "outside_pack": 3, "weeks": 4, "never_found": false, "best_absolute_rank": 3}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "dental implants plano", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Family Dental Plano", "rank_absolute": 4, "review_count": 310, "average_rating": 4.3, "photo_count": 134}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “emergency dentist plano”

Local visibility - score 61/100. Evidence confidence: medium.

This keyword missed the local pack in 3 of 4 consecutive checks, best observed position 1.

Check the result URL and listing relevance for “emergency dentist plano” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "emergency dentist plano", "outside_pack": 3, "weeks": 4, "never_found": false, "best_absolute_rank": 1}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "emergency dentist plano", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “family dentistry plano”

Local visibility - score 61/100. Evidence confidence: medium.

This keyword missed the local pack in 3 of 4 consecutive checks, best observed position 1.

Check the result URL and listing relevance for “family dentistry plano” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "family dentistry plano", "outside_pack": 3, "weeks": 4, "never_found": false, "best_absolute_rank": 1}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "family dentistry plano", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).

### [warning] Outside the local pack for “teeth whitening plano”

Local visibility - score 61/100. Evidence confidence: medium.

This keyword missed the local pack in 3 of 4 consecutive checks, best observed position 3.

Check the result URL and listing relevance for “teeth whitening plano” on mobile. Compare observed competitors and verify service relevance before changing anything.

Limit: Sampled positions depend on query, device and geography. Competitor differences are descriptive and do not establish why they rank.

- ranks: Count weeks outside local pack in 4 consecutive checks. Values: `{"keyword": "teeth whitening plano", "outside_pack": 3, "weeks": 4, "never_found": false, "best_absolute_rank": 3}`. 4 source records (IDs and full rows in JSON).
- keywords: Keyword and device context. Values: `{"keyword": "teeth whitening plano", "device": "mobile"}`. 1 source records (IDs and full rows in JSON).
- competitors: Rivals ahead on the same keyword and latest week. Values: `{"ahead": 1, "rivals": [{"competitor_name": "Premier Dental Care", "rank_absolute": 1, "review_count": 218, "average_rating": 3.9, "photo_count": 29}]}`. 1 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “brightpath dental plano”

Local visibility - score 61/100. Evidence confidence: medium.

“brightpath dental plano” fell 50%, from 4,154 (2026-07) to 2,087 impressions (2026-08).

Inspect the listing and relevant website page for “brightpath dental plano”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "brightpath dental plano", "previous": 4154, "current": 2087, "lost_impressions": 2067, "decline_share": 0.4976, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [warning] Lost search visibility for “dentist near me”

Local visibility - score 52/100. Evidence confidence: medium.

“dentist near me” fell 35%, from 647 (2026-07) to 419 impressions (2026-08).

Inspect the listing and relevant website page for “dentist near me”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "dentist near me", "previous": 647, "current": 419, "lost_impressions": 228, "decline_share": 0.3524, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Lost search visibility for “best dentist near me dallas”

Local visibility - score 44/100. Evidence confidence: medium.

“best dentist near me dallas” fell 24%, from 2,440 (2026-07) to 1,862 impressions (2026-08).

Inspect the listing and relevant website page for “best dentist near me dallas”. Confirm actual services and compare demand before changing copy or categories.

Limit: Search-term reporting is truncated. Missing terms are not treated as zero; this does not establish demand or a service the business offers.

- search_terms: Compare same exact term in consecutive complete months. Values: `{"search_term": "best dentist near me dallas", "previous": 2440, "current": 1862, "lost_impressions": 578, "decline_share": 0.2369, "threshold": 0.2}`. 2 source records (IDs and full rows in JSON).

### [notice] Confirm unset attributes with the location manager

Profile completeness - score 27/100. Evidence confidence: medium.

3 of 34 category attributes are unset (9%).

Review these available attributes; record true or false only after confirmation: transgender_safespace, payment_plans_available, kids_area.

Limit: Availability does not mean applicability. Never enable unsupported services.

- catalog: Catalog minus assigned attribute names. Values: `{"available": 34, "unset": 3, "unset_share": 0.0882, "missing": ["transgender_safespace", "payment_plans_available", "kids_area"]}`. 34 source records (IDs and full rows in JSON).
- attributes: Explicit FALSE counts as configured. Values: `{"assigned": 31}`. 31 source records (IDs and full rows in JSON).

Coverage:

- profile: clear - Essential profile fields are populated.
- attributes: triggered - 3 of 34 category attributes are unset.
- media: clear - No explicitly missing profile or cover image.
- posts: clear - A post falls within the configured recency window.
- reviews: clear - No qualifying unanswered critical reviews.
- booking_followup: triggered - 5 requests still say new after 2 days.
- booking_outcomes: triggered - 17 of 37 settled past visits did not happen (46%).
- performance: clear - Largest measured fall 0.4% is below the 10% reporting floor.
- search: triggered - 5 of 11 matched terms fell at least 20%, losing 5,072 impressions.
- rankings: triggered - 5 of 12 evaluated keywords missed the local pack in at least 3 of 4 consecutive checks.
