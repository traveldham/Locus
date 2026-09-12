# Locus Workspace Memory

Last updated: 2026-09-13

## Workspace structure

- `frontend/`: Next.js 16 / React 19 / TypeScript / Tailwind CSS 4 application, adapted from a NextAdmin v2 template.
- `backend/`: FastAPI application — auth, organizations, Google OAuth, and the Google Business Profile integration.
- `locus-intelligence-assignment/`: the original take-home brief and 14 sample CSV files. Now used as **sample data**, not as the roadmap.
- `researched/`: two research documents on the GBP API surface, data mapping and recommendation-engine architecture. The GBP API document is accurate and is the basis for the current build.
- `tasks/`: working task documentation — status board, architecture, roadmap, and one file per unit of work.

## Objective

Build an end-to-end **Google Business Profile management platform**: a business connects their Google account once, we discover the locations that account manages, they import a selection into a named Project, and then they manage those profiles — details, hours, attributes, photos, posts, reviews — across many locations from one dashboard.

## Scope change (2026-09-12)

The user explicitly dropped the recommendation/ML engine from current scope and redirected to the management platform. The earlier framing in `FOUNDATION_PLAN.md` and in `researched/GBP_Recommendation_Engine_Architecture.md` describes work that is **not being built right now**. Treat the assignment deliverables as historical context.

## Current state

- Backend foundation complete and verified: 15 tables, models and schemas split into packages, Fernet token encryption, signed OAuth state, Alembic head `20260913_0002`.
- Google sign-in and organization onboarding endpoints built with tests.
- GBP connect / discovery / import, the Projects and Locations APIs, and the corresponding UI were in flight at the time of writing — see `tasks/STATUS.md` for the live board.
- Nothing has been exercised end to end against a running system. The migration has never been applied to Postgres.

## Established constraints

- **Google has not approved this app for Business Profile API access.** Unapproved Cloud projects sit at 0 QPM, so every live GBP data call fails. Approval requires a real verified Business Profile managed 60+ days, a business website, and roughly two weeks of review.
- All Google data flows through a provider abstraction with a single live implementation. There is deliberately **no fixture or demo dataset in the product**: an unapproved call fails with a clear 403/quota error rather than showing invented businesses. Made-up data lives only in `backend/tests/stubs.py`.
- Google sign-in (`openid email profile`) and Business Profile access (`business.manage`) are **separate grants**. Bundling them would block login until app verification completes.
- Reviews, posts and media are still only available on the legacy `mybusiness.googleapis.com/v4` endpoints. Everything else has moved to split v1 services. Both location ID forms are therefore stored.
- `readMask` is required on Business Information reads; `updateMask` is required on writes, and `validateOnly=true` gives a dry run.
- Profile writes must be previewed, explicitly approved by a person, and recorded in `ProfileAction`. Automated changes without specific consent are against Google's policy, as is auto-reverting Google's own updates.
- Google API Content has storage restrictions. The schema separates refreshable Google Content from our own permanent derived and audit data. Needs legal review before any permanent data lake.
- The dataset in `locus-intelligence-assignment/` is synthetic; do not research a real business matching its name.

## Working agreements

- Do not start the frontend or backend dev servers. The user runs them and reports errors back. Lint, typecheck and tests are expected.
- Keep the codebase structured — small focused modules, no dumping-ground files.

## Next steps

1. Register the new routers in `app/main.py` and run a full backend and frontend verification pass.
2. User actions: register both OAuth redirect URIs, submit the GBP Basic API Access application, run `alembic upgrade head`.
3. Visual pass over the new UI once running.
4. Profile write path with preview, approval and audit (task 012) once live API access is available.

A background sync engine (arq worker, Redis, token-bucket pacing) was built and then
deliberately removed: the project's Google quota is zero and the owner manages one
business, so pacing a non-existent quota through a queue was pure weight. Discovery and
review sync run inline and still record a `SyncRun` row each. Do not reintroduce it
without a real quota and a real fleet of locations.

## Handoff log

- 2026-09-13: Closed the data-to-UI omissions audit. Added a paginated/filterable Posts API and `/posts` UI for all 69 seeded posts. Also surfaced location coordinates/resource metadata and timestamps, booking external IDs, keyword result URLs, competitor Place IDs, and attribute value types. Verification: backend pytest/ruff and frontend ESLint/TypeScript.

- 2026-09-12: Analysed the assignment brief, `DATA.md` and all 14 CSVs. Confirmed the dataset is largely Google Business Profile data — `locations.csv` carries `gbp_location_id`, and `location_daily_kpis.csv` maps one-to-one onto the Performance API's daily metrics.
- 2026-09-12: Built the FastAPI foundation — auth, organizations, memberships, migrations — and adapted the frontend template into a branded application shell.
- 2026-09-12: Brand pass on the frontend — favicon wired to `public/brand/favicon.webp`, maroon `#44131B` auth panel, sidebar collapsed by default with hover-to-expand showing the favicon collapsed and the full logo expanded. Fixed a Turbopack root-resolution failure caused by an unrelated `package-lock.json` in the user's home directory, by pinning `turbopack.root` in `next.config.ts`.
- 2026-09-12: **Scope redirected** from the recommendation engine to the GBP management platform. Verified the current API surface against live documentation: reviews and replies remain v4-only, `readMask`/`updateMask` are mandatory, Q&A was discontinued in November 2025.
- 2026-09-12: Backend data foundation landed and verified. Models and schemas restructured into packages; 11 new tables; `users.password_hash` made nullable for Google-only accounts. Dropped `google-auth` in favour of PyJWT + JWKS for ID-token verification, avoiding a second HTTP stack.
- 2026-09-12: Google OAuth primitives written (`app/services/google/oauth.py`). Note: `offline=True` forces `prompt=consent` because Google returns a refresh token only on fresh consent — without it the stored connection silently dies with its first access token.
