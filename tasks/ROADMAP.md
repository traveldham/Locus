# Roadmap

End-to-end build order for the GBP management platform.

**Legend:** ✅ done · 🔨 in progress · ⬜ planned · ⛔ blocked on Google API approval

---

## Parallel track — Google API access (start immediately, blocks nothing below until Phase 3)

| Item | Notes |
|---|---|
| ⬜ Basic API Access application | Needs a real verified GBP managed 60+ days, plus a business website. ~2 week review. Unapproved projects sit at 0 QPM. |
| ⬜ OAuth client redirect URIs | `http://localhost:8000/api/v1/auth/google/callback` and `http://localhost:8000/api/v1/integrations/google/callback` |
| ⬜ Consent screen | External → Testing, with the developer added as a test user |
| ⬜ App verification | Required before external users can grant `business.manage` |

---

## Phase 1 — Connect

| # | Step | Status |
|---|---|---|
| 001 | Backend data foundation: models, schemas, migration, crypto, OAuth state | ✅ |
| 002 | Google sign-in + organization onboarding | 🔨 |
| 003 | GBP connect, provider abstraction, discovery, import | 🔨 |
| 004 | Projects and Locations APIs | 🔨 |
| 005 | Auth + onboarding UI | ✅ |
| 006 | Integrations page + discovery/import wizard UI | 🔨 |
| 007 | Projects + Locations UI | 🔨 |
| 008 | Router wiring, end-to-end verification | ⬜ |

## Phase 2 — Keep data current

| # | Step | Status |
|---|---|---|
| 009 | Sync engine — worker (arq + Redis), `SyncRun` tracking, pacing, retry with backoff and jitter | ⬜ |
| 010 | Scheduled refresh: daily performance, periodic profile, monthly search terms | ⬜ |

## Phase 3 — Manage the profile (the core product)

| # | Step | Status |
|---|---|---|
| 011 | Location profile read — full detail from live Google data | ⛔ |
| 012 | Location profile write — `locations.patch` + `updateMask`, `validateOnly` preview, `ProfileAction` audit | ⛔ |
| 013 | Attributes editor driven by the per-category attribute catalog | ⛔ |
| 014 | Hours editor supporting multiple periods per day, overnight spans, special hours | ⛔ |

## Phase 4 — Engagement surfaces

| # | Step | Status |
|---|---|---|
| 015 | Reviews inbox across all locations + reply / edit reply / delete reply (**v4 API**) | ⛔ |
| 016 | Posts — create, edit, delete; standard / event / offer / alert with CTAs (**v4 API**) | ⛔ |
| 017 | Media — upload, categorise, delete (**v4 API**) | ⛔ |
| 018 | Place action links — booking / appointment / order URLs | ⛔ |

## Phase 5 — Insight

| # | Step | Status |
|---|---|---|
| 019 | Performance dashboards — `fetchMultiDailyMetricsTimeSeries` | ⛔ |
| 020 | Monthly search keywords — preserve the `value` vs `threshold` distinction | ⛔ |
| 021 | Verification / Voice of Merchant state and owner-initiated verification | ⛔ |

## Phase 6 — Scale and automation

| # | Step | Status |
|---|---|---|
| 022 | Pub/Sub notifications — new review, updated review, Google update, customer media, VOM change | ⛔ |
| 023 | Google suggested updates — show the diff, let the owner accept or reject (never auto-revert; prohibited) | ⛔ |
| 024 | Bulk multi-location operations, paced against the 10 edits/minute/profile quota | ⛔ |
| 025 | Roles and permissions, audit log UI, connection health and quota dashboards | ⬜ |

---

## Known gaps — Google's own dashboard can do these, the API cannot

Do not promise these. Deep-link to Google instead, using each location's `maps_uri` / `new_review_uri`.

- Questions & Answers (that API was discontinued in November 2025)
- Customer messaging / chat
- Deleting a customer review, or removing customer-uploaded photos (flagging is Google's UI only)
- Creating a new profile, claiming ownership, transferring ownership
- Appealing a suspended profile
- Post-level view counts (removed from the modern Performance API)

## Not available from Google at all

These need separate paid providers and must never be presented as Google data:

- Keyword rank tracking and local-pack position
- Competitor benchmarking
- Individual customer booking records (Google gives only the aggregate `BUSINESS_BOOKINGS` metric)
