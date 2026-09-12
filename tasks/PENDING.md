# Pending

Everything not yet done, split into **what you do** and **what I build**.

Last updated: 2026-09-12

---

# Part 1 — Your actions

These are the only things blocking the project. Nothing I build can replace them.

## 1. Apply for Google Business Profile API access — DO THIS FIRST

This is the long pole. Roughly **two weeks** of review, and everything live depends on it.

**Prerequisites you must already have:**

| Requirement | Notes |
|---|---|
| A real Google Business Profile | Brightpath Dental is synthetic and cannot be used |
| Verified, and managed for **60+ days** | This is the one people fail on |
| A website for that business | Must match the profile |
| A Google Cloud project | The same one holding your OAuth client |
| A Business Profile organization account | Created from the Business Profile side |

**Steps:**
1. Go to the Business Profile APIs **Basic API Access** request form (linked from <https://developers.google.com/my-business/content/prereqs>).
2. Submit using the real verified business, not the sample data.
3. Wait for approval. Google replies by email.

**How to tell it worked:** in Cloud Console → APIs & Services → Quotas, the Business Profile APIs move from **0 QPM** to roughly **300 QPM**. A quota of 0 means not approved — do **not** file a quota-increase request to fix that; it is the wrong form and will be rejected.

## 2. Configure the OAuth client in Google Cloud Console

**Authorized redirect URIs** — add both exactly:

```
http://localhost:8000/api/v1/auth/google/callback
http://localhost:8000/api/v1/integrations/google/callback
```

**Authorized JavaScript origin:**

```
http://localhost:3000
```

**OAuth consent screen:** User type **External**, publishing status **Testing**, and add your own Google account under **Test users**. Without that last step Google refuses the sign-in with a 403.

**Enable these APIs** in the same project:
- My Business Account Management API
- My Business Business Information API
- Business Profile Performance API
- My Business Notifications API
- My Business Verifications API
- My Business Place Actions API

They will enable but return 0 quota until step 1 is approved. That is expected.

**Note on app verification:** `business.manage` is a Google-restricted scope. In Testing mode your own test accounts can consent. Before *other people* can connect, the app needs Google's OAuth verification — a separate review from step 1. Not needed for development.

## 3. Run the database migration

Never been run. This is the first unexercised path.

```bash
cd backend
uv run alembic upgrade head
```

Expected head: the reviews revision, on top of `20260913_0002`.

## 4. Start both apps and tell me what breaks

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Then walk this path and report anything wrong:

1. Register with email/password → land on the dashboard
2. Sign out, then **Continue with Google** → onboarding → name your organization
3. Settings → Integrations → Connect
4. **Find my locations** → 12 clinics appear with status chips
5. Select some → name a project → Import
6. Projects → open it → Locations → open one → check hours, attributes, Google status
7. Edit a field → Preview → confirm → check the change history
8. Reviews → filter to unreplied → write a reply

Steps 1–8 all work on fixture data. None of them need Google approval.

## 5. Optional — Redis

Only if you want background sync rather than inline. Everything works without it.

```bash
brew install redis && brew services start redis
# then set REDIS_URL in backend/.env
```

---

# Part 2 — What I still need to build

## In progress right now

| # | Task |
|---|---|
| 010 | Profile editing — preview, apply, audit (backend + UI) |
| 011 | Reviews — model, provider, reply API, inbox UI |
| 009 | Sync engine — background worker, scheduled refresh, quota pacing |

## Next, buildable without Google approval

| # | Task | Why it matters |
|---|---|---|
| 012 | **Posts** — create, edit, delete; standard / event / offer, CTA buttons | Main outbound marketing surface |
| 013 | **Media** — upload, categorise, delete photos and video | Photo count strongly affects profile performance |
| 014 | **Attributes editor** driven by the per-category catalog | Attributes vary by category and country; cannot be hardcoded |
| 015 | **Bulk operations** — apply hours, attributes or a post across many locations | The reason a multi-location product exists. Must pace against 10 edits/min/profile |
| 016 | **Performance dashboards** — impressions, calls, directions, clicks | Read-only, so lower risk |
| 017 | **Special hours** — holiday overrides | Most-requested seasonal edit |
| 018 | **Team roles and permissions** | Who may edit a live profile vs only view |
| 019 | **Connection health** — token expiry, re-auth prompts, quota visibility | Silent auth failure is the worst failure mode |

## Blocked until approval

| # | Task |
|---|---|
| 020 | Swap `GBP_PROVIDER` to `live` and reconcile real responses against the fixtures |
| 021 | Verification / Voice of Merchant state and owner-initiated verification |
| 022 | Pub/Sub notifications — real-time new review, Google update, customer media |
| 023 | Google suggested updates — show the diff, accept or reject per field |

---

# Part 3 — Things that can never be built

Not scope decisions. Google provides no API. Do not promise these; deep-link to Google instead via each location's `maps_uri`.

- Questions & Answers — that API was discontinued in November 2025
- Customer messaging / chat
- Deleting a customer's review, or removing customer-uploaded photos
- Creating a profile, claiming or transferring ownership
- Appealing a suspended profile
- Post-level view counts

## Needs a different paid provider, not Google

- Keyword rank tracking and local-pack position
- Competitor benchmarking
- Individual customer bookings — Google gives only the aggregate `BUSINESS_BOOKINGS` number
