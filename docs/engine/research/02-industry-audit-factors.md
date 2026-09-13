# 02 — Industry audit factors for a Google Business Profile audit engine

Research date: 2026-09-13. Scope: what leading local-SEO sources say a best-in-class GBP audit checks, and which factors move local-pack ranking vs. conversion.

Sourcing note: `whitespark.ca` and most `brightlocal.com` pages return HTTP 403 to automated fetchers. Whitespark's own ranking-factors page could not be read directly; its numbers below are taken from secondary write-ups that quote the 2026 report, and where those write-ups disagree the range is shown. BrightLocal's 2025 Local Consumer Review Survey *was* retrieved in full (via text proxy) and is cited directly; BrightLocal 2026 figures come from third-party summaries of the survey.

---

## 1. Whitespark Local Search Ranking Factors 2026 (published 2025-11-06)

Primary URL: https://whitespark.ca/local-search-ranking-factors/ (47 expert contributors, 187 individual factors scored; a new "AI search visibility" category was added this edition).

### Thematic weights, Local Pack / Maps

| Signal group | Weight (as quoted) |
|---|---|
| Google Business Profile signals | 32% |
| Review signals | 16–20% (secondary sources disagree; most quote 20%) |
| On-page signals | 15–19% |
| Link signals | 8–15% |
| Behavioral signals | 8–9% |
| Citation signals | 6–7% |

Sources quoting the report: https://usamahabib.com/local-seo-ranking-factors/ (32 / 20 / 15 / 9 / 8 / 6), https://w3marketinghub.com/seo/local-seo-ranking/ (32 / ~20 / 19 / 15 / 8 / 7), https://biziq.com/blog/local-seo-statistics/ (32 / 16 / 19 / 15 / 8 / 7), https://gbppromote.com/local-search-pack-ranking-factors/.

### Top individual Local Pack factors

Ranked with the report's factor scores where a source quotes them:

1. Primary GBP category — score 227 (https://www.mbadv.agency/google-business-profile/optimizing-business-categories-for-better-visibility)
2. Proximity of the business address to the searcher — 225 (same)
3. Keywords in the GBP business title — 223 (same; https://usamahabib.com/local-seo-ranking-factors/ lists business name "third")
4. Review recency / velocity — reported as a top-5 factor by Darren Shaw and a new top-10 entry (https://uberall.com/en-us/resources/local-beat/master-local-seo-whitespark; https://whitespark.ca/blog/the-most-underrated-local-ranking-factor-in-2025/)
5–6. "Business is open at time of search" — quoted as #5 by https://w3marketinghub.com/seo/local-seo-ranking/ and https://usamahabib.com/local-seo-ranking-factors/, #6 by https://www.mbadv.agency/google-business-profile/optimizing-business-categories-for-better-visibility
7. Physical address in the city of search (storefronts) — https://usamahabib.com/local-seo-ranking-factors/

Other factors the report and Whitespark commentary elevate: additional GBP categories (up to 9 extra), GBP services field, quality/authority of inbound links, dedicated page per service (#1 in Localized Organic and #2 in AI Visibility per https://harmo.me/en/blog/local-seo-ranking-factors-2026-whitespark), and behavioral engagement (posts, photos, clicks, calls, direction requests, review cadence — all described as "climbing" per https://www.soci.ai/blog/local-memo-local-ranking-factors-of-2026-have-arrived/). Social signals and AI-search signals appear as ranking factors for the first time in 2026 (same SOCi source).

### Top negative factors (2026)

As quoted by https://gmbapi.com/news/local-ranking-factors-comparison-2026-2023/ and https://storerocket.io/learn/local-seo-ranking-factors: PO box / virtual-office address (#1); incorrect primary category (#2, penalty score 214); "permanently closed" flag on an open business; keyword-stuffed business name; fake reviews and review gating; low 1–2 star ratings; malware on the website; incorrect map-pin placement.

### Google's own statement

Google names three ranking inputs — relevance, distance, prominence — and says "Businesses with complete and accurate info are more likely to show up in local search results," specifically listing full address, hours including special hours, photos, and reviews plus replies. https://support.google.com/business/answer/7091

---

## 2. Consolidated audit checklist

Each check lists the benchmark/threshold a source gives and the source URL. "Ranking" vs "conversion" indicates what the evidence supports.

### Profile completeness

| Check | Benchmark / threshold | Source |
|---|---|---|
| Primary category matches the core business | #1 local-pack factor (score 227); wrong primary category is #2 negative factor (214) | https://usamahabib.com/local-seo-ranking-factors/ ; https://gmbapi.com/news/local-ranking-factors-comparison-2026-2023/ |
| Additional categories set | Up to 9 additional categories available; re-check Sterling Sky's category list for new categories each audit | https://www.mbadv.agency/google-business-profile/optimizing-business-categories-for-better-visibility ; https://searchengineland.com/guide/local-seo-audit |
| Business name matches real-world signage/legal name; no added keywords | Keywords in name = #3 factor but adding them without a DBA violates guidelines and risks hard suspension | https://www.sterlingsky.ca/google-business-name-ranking/ ; https://searchengineland.com/guide/local-seo-audit |
| Address is a real staffed location (not PO box / virtual office); address shown, not hidden, where eligible | PO box/virtual office = #1 negative factor; hidden address correlated negatively with "near me" rank | https://gmbapi.com/news/local-ranking-factors-comparison-2026-2023/ ; https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/ |
| Map pin placed correctly | Incorrect pin is a listed negative factor | https://searchengineland.com/guide/local-seo-audit ; https://storerocket.io/learn/local-seo-ranking-factors |
| Phone number present and correct; website URL points to the right landing page | SEL audit item | https://searchengineland.com/guide/local-seo-audit |
| Services field populated (all predefined services + custom) | Ranking impact seen within 24–72 h; earlier test measured 2–5% lift for service keywords; "most businesses leave this empty" | https://www.sterlingsky.ca/services-in-google-business-profile-impact-ranking/ ; https://uberall.com/en-us/resources/local-beat/master-local-seo-whitespark |
| Products / menu populated | SEL and SEJ audit items | https://searchengineland.com/guide/local-seo-audit ; https://www.searchenginejournal.com/local-seo-audit-checklist/437842/ |
| Business description filled | Conversion only; "should not impact rankings at all" | https://www.sterlingsky.ca/services-in-google-business-profile-impact-ranking/ |
| Attributes complete; social profile links added | SEL audit items | https://searchengineland.com/guide/local-seo-audit |
| Overall completeness | Google: complete profiles "more likely to show up"; secondary stats claim ~2.1x more actions and 70% more likely to attract visits for complete profiles | https://support.google.com/business/answer/7091 ; https://newmedia.com/blog/google-business-profile-statistics |

### Reputation

| Check | Benchmark / threshold | Source |
|---|---|---|
| Average rating | 38% of consumers require ≥4.0 (BrightLocal 2025); 2026 summaries report 68% require ≥4.0 and 31% require ≥4.5 (up from 17%) | https://www.brightlocal.com/research/local-consumer-review-survey-2025/ ; https://gbppromote.com/local-consumer-review-survey/ |
| Review count | 10 reviews is a measurable ranking step ("magic 10"); consumers: 33% want 20–49, 47% won't use a business with <20 (2026) | https://www.sterlingsky.ca/number-of-reviews-impact-ranking/ ; https://starfish.reviews/online-review-statistics/ ; https://gbppromote.com/local-consumer-review-survey/ |
| Review recency / velocity | Rankings drop after 3–4 weeks with no new review; target = top competitor's monthly rate + 1; 74% of consumers want reviews from last 3 months | https://whitespark.ca/blog/the-most-underrated-local-ranking-factor-in-2025/ ; https://uberall.com/en-us/resources/local-beat/master-local-seo-whitespark ; https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/ ; https://gbppromote.com/local-consumer-review-survey/ |
| Reviews with text vs star-only | Text reviews "had a stronger impact on rankings"; 1-star with no text doesn't even display in Maps app | https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/ |
| Owner response rate | 89% expect a response; 80% more likely to use a business that answers every review; 42% unlikely to use one that never replies | https://gbppromote.com/local-consumer-review-survey/ |
| Response time | BrightLocal 2025: respond within a week (63% expect 2–3 days to a week; only 7% expect none). 2026: 19% same-day, 32% next-day, 81% within a week. GatherUp: 86% of complainers expect a reply within 3 days | https://www.brightlocal.com/research/local-consumer-review-survey-2025/ ; https://www.replyonthefly.com/blog/google-review-response-time-study ; https://gatherup.com/blog/software-to-reply-to-reviews-customer-feedback/ |
| Response quality (non-templated) | 50% discouraged by generic/templated replies | https://www.pinmeto.com/news/brightlocal-local-consumer-review-survey-2026/ |
| Negative-review handling | 66% trust more when a business offers to make things right; 64% when the owner apologises | https://www.replyonthefly.com/blog/google-review-response-time-study (citing GatherUp) |
| Sudden count drops / rating spikes; sentiment trends | Flag drops (bugs/penalties) and suspicious spikes; track emerging negative themes | https://searchengineland.com/guide/local-seo-audit |
| Fake / incentivised reviews | Negative ranking factor; 46% of consumers suspect AI-written reviews, 42% suspect paid ones | https://gmbapi.com/news/local-ranking-factors-comparison-2026-2023/ ; https://www.brightlocal.com/research/local-consumer-review-survey-2025/ |

### Local visibility

| Check | Benchmark / threshold | Source |
|---|---|---|
| Proximity / service-area coverage | #2 factor (225); ~55% of pack decisions attributed to proximity by some summaries | https://www.mbadv.agency/google-business-profile/optimizing-business-categories-for-better-visibility ; https://gbppromote.com/local-search-pack-ranking-factors/ |
| NAP consistency across structured citations (Yelp, Apple Maps, TripAdvisor, BBB) | Citation signals 6–7% of pack weight; audit accuracy and missing fields | https://searchengineland.com/guide/local-seo-audit ; https://usamahabib.com/local-seo-ranking-factors/ |
| Unstructured citations | Search brand across first 4–5 organic pages; verify accuracy | https://searchengineland.com/guide/local-seo-audit |
| Duplicate listings | SEJ / SEL audit item | https://www.searchenginejournal.com/local-seo-audit-checklist/437842/ |
| Landing-page content depth and dedicated service pages | More meaningful words on landing page correlated with rank; "dedicated page per service" #1 localized-organic factor | https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/ ; https://harmo.me/en/blog/local-seo-ranking-factors-2026-whitespark |
| Inbound / local links | Link signals 8–15% of pack weight | https://w3marketinghub.com/seo/local-seo-ranking/ |
| Local-pack rank for target keywords vs top-10 competitors | BrightLocal's GBP Audit tool benchmarks against top 10 for up to 5 terms | https://help.brightlocal.com/hc/en-us/articles/360025649253-What-is-Google-Business-Profile-Audit |

### Operations

| Check | Benchmark / threshold | Source |
|---|---|---|
| Hours accurate; special/holiday hours set | "Open at time of search" is a top-5/6 pack factor; ranking effects begin approaching closing time | https://w3marketinghub.com/seo/local-seo-ranking/ ; https://uberall.com/en-us/resources/local-beat/master-local-seo-whitespark |
| Not flagged "permanently closed" / temporarily closed in error | Listed negative factor | https://gmbapi.com/news/local-ranking-factors-comparison-2026-2023/ |
| Q&A monitored and answered; seed FAQs | 91% of questions unanswered by owners (43k-profile study); many are time-sensitive ("are you open today?") | https://searchengineland.com/google-qa-more-than-90-percent-of-questions-unanswered-by-business-owners-312879 |
| Verification status, ownership access, suspension risk | GBP audit definitions | https://agencyanalytics.com/blog/google-business-profile-audit |
| Website reachable, no malware | Malware is a listed negative factor | https://storerocket.io/learn/local-seo-ranking-factors |
| Regular audit cadence | Compare to prior audit at ~3-month intervals | https://searchengineland.com/guide/local-seo-audit |

### Performance

| Check | Benchmark / threshold | Source |
|---|---|---|
| Actions per month (calls, directions, website clicks) | Median ~59 actions/month; mix ≈56% website, 24% calls, 20% directions | https://www.brightlocal.com/research/google-my-business-insights-study/ (via https://searchlab.nl/en/statistics/google-business-profile-statistics-2026) |
| View-to-action rate | ~5% of views lead to an action | https://searchlab.nl/en/statistics/google-business-profile-statistics-2026 |
| Trend on calls / directions / bookings | Downtrends flag listing or competitive issues | https://searchengineland.com/guide/local-seo-audit |
| Behavioural engagement (CTR, clicks-to-call, dwell) | 8–9% of pack weight, "climbing" | https://www.soci.ai/blog/local-memo-local-ranking-factors-of-2026-have-arrived/ |
| Measure conversions, not rank alone | Shaw: "You don't think about rankings. You just think about general visibility" | https://uberall.com/en-us/resources/local-beat/master-local-seo-whitespark |

### Content

| Check | Benchmark / threshold | Source |
|---|---|---|
| Photo count | Median listing has 11 photos; 100+ photos correlated with 520% more calls and 2,717% more direction requests; single-photo listings get 65% fewer clicks; at least 3 photos per type | https://www.brightlocal.com/research/google-my-business-insights-study/ (via https://www.vendasta.com/blog/google-business-photos/ and https://searchlab.nl/) |
| Photo presence | Profiles with photos get 42% more direction requests and 35% more website clicks (Google figure) | https://newmedia.com/blog/google-business-profile-statistics |
| Photo freshness / velocity | Track "By Owner" upload rate vs top competitor; remove spam or embarrassing imagery | https://searchengineland.com/guide/local-seo-audit |
| Photo quality/relevance | Larger, relevant images helped rank; effect industry-dependent (restaurants/salons yes, garage doors negligible) | https://www.sterlingsky.ca/do-images-impact-ranking-on-google/ ; https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/ |
| Posting cadence | At least weekly; weekly vs monthly ≈ 28% more actions; offer posts and urgency/discount posts get most clicks; ~1.09% avg post CTR | https://www.lawrencehitches.com/google-business-profile-posts/ ; https://searchlab.nl/en/statistics/google-business-profile-statistics-2026 ; https://www.sterlingsky.ca/google-posts/ |
| Post recency | Regular posts contribute to "freshness"/behavioural signals | https://uberall.com/en-us/resources/local-beat/master-local-seo-whitespark |
| Description, services and menu text quality | Conversion elements; audit for completeness | https://searchengineland.com/guide/local-seo-audit |

---

## 3. What customers act on

Rating thresholds
- 38% of consumers require a minimum 4.0 average; a further 4% year-on-year say rating doesn't affect them at all (BrightLocal 2025). https://www.brightlocal.com/research/local-consumer-review-survey-2025/ ; https://starfish.reviews/online-review-statistics/
- 2026: 68% require ≥4.0, 31% require ≥4.5 (from 17%), 10% insist on 5.0. https://gbppromote.com/local-consumer-review-survey/
- 85% more likely to use a business after positive reviews; 77% deterred by negative ones (2026, n=1,002). https://www.pinmeto.com/news/brightlocal-local-consumer-review-survey-2026/

Review count and recency
- 33% need 20–49 reviews; 22% need 50–99; 15% say count has no impact (2025). https://starfish.reviews/online-review-statistics/
- 20% say reviews must be ≤2 weeks old (down 7 pts); ~10% say recency doesn't matter (2025). https://www.brightlocal.com/research/local-consumer-review-survey-2025/
- 2026: 74% want reviews from the last 3 months; 44% from the last month. https://gbppromote.com/local-consumer-review-survey/

Reply expectations
- Only 7% expect no response; 63% expect a reply within 2–3 days to a week (2025). https://www.brightlocal.com/research/local-consumer-review-survey-2025/
- Over 80% think businesses should respond to all reviews, yet >40% would still visit a non-responder (2025). https://localsearchforum.com/threads/brightlocals-2025-consumer-review-study.62172/
- 2026: 89% expect a reply; 19% same-day, 32% next-day, 81% within a week; 80% more likely to use a business that replies to all; 50% put off by templated replies. https://gbppromote.com/local-consumer-review-survey/
- 86% of complainers expect a response within 3 days; 89% read owner responses (GatherUp). https://gatherup.com/blog/software-to-reply-to-reviews-customer-feedback/
- Industry actuals: high-visibility brands respond to 80.5% of reviews in a median 2.1 days; average brands 45.1% in 6 days (SOCi LVI 2024). https://www.replyonthefly.com/blog/google-review-response-time-study

Photos and profile completeness on clicks / directions
- Photos present: +42% direction requests, +35% website clicks (Google, widely cited). https://newmedia.com/blog/google-business-profile-statistics
- 100+ photos: +520% calls, +2,717% direction requests, +1,065% website clicks vs average (BrightLocal, 45,264 listings). https://www.vendasta.com/blog/google-business-photos/ ; https://searchlab.nl/en/statistics/google-business-profile-statistics-2026
- 74% of consumers check two or more review sites; Google used by 83% (2025), 71% (2026) with AI tools rising to 45%. https://www.brightlocal.com/research/local-consumer-review-survey-2025/ ; https://gbppromote.com/local-consumer-review-survey/
- Trust in reviews equal to personal recommendations fell from 79% (2020) to 42% (2025). https://www.brightlocal.com/research/local-consumer-review-survey-2025/

---

## 4. Myths / things experts say do NOT move ranking

- Google Posts do not affect local-pack rank. Sterling Sky posted weekly for 9 weeks across 3 listings tracking 441 keywords: "no noticeable change in rankings." Posts are for conversion. https://www.sterlingsky.ca/do-google-posts-impact-ranking/
- Q&A keywords do not affect rank. "Adding keywords to the Q&A section of GMB did not have any impact on ranking." https://www.sterlingsky.ca/does-gmb-qa-impact-ranking/
- Business description does not affect rank: "should not impact your rankings at all." https://www.sterlingsky.ca/services-in-google-business-profile-impact-ranking/
- Total review count matters less than monthly consistency; after the 10-review step, adding an 11th showed no bump. https://www.sterlingsky.ca/number-of-reviews-impact-ranking/ ; https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/
- Bursty review campaigns (e.g. every six months) do not sustain rank; steady cadence does. https://whitespark.ca/blog/the-most-underrated-local-ranking-factor-in-2025/
- Hiding the address as a service-area business (even though Google suggests it) correlated negatively with "near me" rank. https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/
- Photo volume has negligible ranking effect in non-visual industries (garage doors), though it strongly affects conversion. https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/
- Keyword-stuffing the business name "works" but is a guideline violation and top negative factor with suspension risk; Google now auto-detects it. https://www.sterlingsky.ca/google-business-name-ranking/ ; https://storerocket.io/learn/local-seo-ranking-factors
- 1-star ratings without text are not even displayed in the Maps app, so their ranking weight is minimal. https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/
- Google itself: "there is no way to request or pay for a better local ranking." https://support.google.com/business/answer/7091
- Whitespark's own myth list (page blocked, listed for follow-up): https://whitespark.ca/blog/10-common-local-seo-myths-debunked/

---

## Implications for the Locus engine (weighting guidance)

1. Ranking-weighted checks: primary category, name compliance, address type/visibility, hours + open-now, services field, review recency (30-day velocity vs competitor), review text share, NAP consistency.
2. Conversion-weighted checks: rating ≥4.0 (warn) / ≥4.5 (target), review count ≥20, response rate and median response time (≤3 days target, ≤7 days floor), non-templated replies, photo count (≥11 median, 100+ top tier), weekly posts, Q&A answered, description/attributes complete.
3. Do not score Posts, Q&A, or description as ranking factors; score them under Content/Operations as conversion hygiene.
