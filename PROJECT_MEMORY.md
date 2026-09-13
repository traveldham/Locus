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

## Scope changes

The user redirected to the management platform on 2026-09-12, then explicitly restored
the changing-data recommendation engine on 2026-09-13. Recommendation code and generated
assignment output are active work, not historical-only scope. The app currently uses
seeded synthetic data, not a live Google connection. Earlier foundation details below
are historical; consult the current backend README and latest handoff entries.

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

- 2026-09-13 (profile audit navigation): Moved the customer-facing current-versus-draft
  profile comparison out of the general recommendation Overview into a dedicated
  `/recommendations/[locationId]/profile` tab. The tab keeps the aligned before/after
  cards and all failing profile checks together, with passed/not-evaluated counts and
  direct “Understand and fix” links. Overview remains focused on score, priorities and
  category status.

- 2026-09-13 (recommendation UX simplification): Reworked issue detail around one
  customer decision per finding: problem/title, what to do, optional AI draft, concise
  evidence explanation, then raw saved rows behind “View source records.” Replaced the
  dense findings table with responsive action cards, made missing drafts explicit when
  business-only facts are required, simplified issue-list language, and labeled AI copy
  as a draft requiring review. Hardened profile AI enrichment: response constraints are
  now enforced in code for contact-free descriptions, project-supported categories,
  catalog-listed unanswered attributes and one suggestion per finding; prompt requests
  shorter summaries and evidence-specific reasons. Added a constraint-rejection test.
  Verification: targeted recommendation tests, ruff, frontend lint/TypeScript/build and
  Impeccable detector. Restart the Celery worker before generating new audits so it loads
  the updated suggestion code.

- 2026-09-13 (recommendation-engine review): Traced the current audit from snapshot
  through Celery, deterministic checks, optional LLM enrichment, API and UI. The profile
  worker currently declares 28 checks across reach/identity/trust/hours/attributes; the
  other five workers still have no checks. Consequently the displayed health score is
  currently the profile score normalized to the whole headline score, while the UI does
  show the other category cards as “No checks built yet.” Found version/output drift:
  `ENGINE_VERSION` remains `3.0.0` although stored `3.0.0` reports contain different
  check inventories; the local database has current runs for only 5 of 12 locations,
  including one old null-score skeleton run. Current suggestion response validation
  checks target rule/field and basic shape, but does not enforce several prompt-only
  constraints (catalog-only attributes, real Google categories, no URLs/phones in
  descriptions). Also, `has_voice_of_merchant = NULL` is currently scored clear and the
  profile card renders it as “Not verified,” instead of treating unknown separately.
  Targeted recommendation verification: 45 tests passed; targeted ruff passed. No code,
  database data, server, worker or generated audit was changed during this review.

- 2026-09-13 (night): **Profile worker built** with 24 deterministic checks in five groups
  (reach, identity, trust, hours, attributes) and a Gemini suggestion layer
  (`services/recommendations/suggestions/`) that drafts description, additional
  categories, attribute answers and name for failed checks, using the profile plus the
  location's projects (name, website, description, services) as context. Suggestions are
  optional: no key, disabled, or an API error is recorded on the worker result and the
  audit still succeeds. Tests never reach a model (conftest forces an unconfigured
  provider). The Gemini Developer API key's project has no prepaid credit (429 on every
  endpoint), so the user switched to **Vertex AI with the device's application default
  credentials**: `suggestions/llm.py` is a provider service (`LLM_PROVIDER=vertex|gemini`),
  `.env` carries `VERTEX_PROJECT=traveldham-d253e`, global endpoint, `gemini-3.8-flash`.
  Live run on LOC-003 and LOC-011 through Vertex: both succeeded in 6-8 s with every
  draftable finding suggested. Docs: `docs/engine/ARCHITECTURE.md`,
  `docs/engine/workers/profile.md`, research under `docs/engine/research/`.

- 2026-09-13: Projects now retain business website_url, description and services JSON list
  alongside the existing name/IDs/status/ownership fields. Migration `20260913_0011`
  applied locally. Create/update/list/detail APIs expose these fields; partial updates
  preserve omitted values, null clears URL/description, [] clears services. HTTP(S)-only
  URL validation, service length/count limits and case-insensitive deduplication added.
  Frontend New project, Edit business details and project detail now capture/show them.
  `app/sample_business.py` derives the demo domain/services from supplied CSVs and fills
  missing metadata during future seeding without replacing operator-entered values.
  Backfilled the six existing Brightpath-linked projects only; kept their names, IDs,
  location memberships and all operational data. No full reseed. Verified 9 project tests,
  targeted ruff, frontend TypeScript/ESLint/build. Existing audit-engine edits preserved.

- 2026-09-13 (evening): **Audit engine reset to a six-worker skeleton.** Decision by the
  user: one audit = one pipeline of six independent category workers (profile,
  reputation, visibility, operations, performance, content; weights 20/20/25/15/10/10),
  every rerun runs all six, each worker's status is tracked on its own and the job's
  progress is the share of workers finished. Removed: all ten previous rules and their
  thresholds, the previous-vs-current comparison, the metrics panel, the organization
  benchmark, the export CLI and the committed assignment output. Kept: snapshot, evidence
  model, verdict states, category-weighted scoring, job queue, API and UI shell. Workers
  live in `backend/app/services/recommendations/categories/` and are empty; the next
  step is building the profile worker in depth, then the other five one at a time.
  Migration `20260913_0010` (applied locally) adds `audit_workers`, moves the snapshot
  onto the job, drops job stage/progress, and deletes old runs. Engine version 3.0.0.
  Verification: 106 backend tests, ruff, tsc and eslint all clean.

- 2026-09-13: Reviews now shows server-total badges for Needs reply, All and Replied.
  The shared count query follows the list's active-project/location/rating/search scope
  and existing reply/remove/sync invalidation. Counts are not page-length counts; stale
  previous-scope values are not carried across filter changes. Mobile badges stack to fit.

- 2026-09-13: Removed sidebar Integrations/empty Settings group; integration details are
  now reached from a header connection-status link on desktop and mobile. It reads the
  shared Google connection query and says “Google account connected” with a small “Demo” label
  for active demo connections. No Search Console integration exists; do not mislabel GBP
  demo data as Search Console connected. Loading, disconnected and error states are shown.

- 2026-09-13: Added Google-style preview as the default location-detail view, with a
  switch back to management and preserved edit workflow. Components:
  `frontend/src/components/locations/preview/`. Overview, all paginated reviews/replies,
  updates and recorded attributes use live application API reads. Operator recommendations
  remain outside the public-style preview and link to the existing location audit.
  Added tenant-scoped `GET /api/v1/reviews/summary`, aggregating all valid stored reviews;
  11 targeted review tests passed, including >200 reviews, changed ratings and tenant isolation.
- 2026-09-13: User explicitly requires Google colors/typography inside the preview,
  **not Locus branding**. `google-profile.module.css` isolates a white Google-style panel,
  blue actions, gray dividers, gold stars, Google Sans headings/controls and Arial body.
  Fonts are locally hosted in `frontend/public/fonts/google-sans/` with OFL and provenance.
  No invented business imagery or live open-now status; synthetic calls/directions disabled.
  Browser checked preview sections, review pagination and management switching. No database
  reseed, public writes, server starts or migrations were needed for the preview.

- 2026-09-13: Closed the data-to-UI omissions audit. Added a paginated/filterable Posts API and `/posts` UI for all 69 seeded posts. Also surfaced location coordinates/resource metadata and timestamps, booking external IDs, keyword result URLs, competitor Place IDs, and attribute value types. Verification: backend pytest/ruff and frontend ESLint/TypeScript.
- 2026-09-13: Completed the full CSV → database → API → UI reconciliation in `tasks/018-csv-database-ui-reconciliation.md`. Added migration `20260913_0005` and persistent storage/UI for all 34 attribute-catalog rows, including unset versus false. Applied the migration and reseeded the local database; all 14 CSV files now have a deliberate visible destination.
- 2026-09-13: Tightened the reconciliation to every CSV column. Migration `20260913_0006` preserves the synthetic `LOC-###` key as `locations.source_location_id`; the UI now also exposes Google review IDs, external keyword IDs, ranking result URLs, search-term location context and competitor Place IDs. Local database is migrated and reseeded through `0006`.

- 2026-09-12: Analysed the assignment brief, `DATA.md` and all 14 CSVs. Confirmed the dataset is largely Google Business Profile data — `locations.csv` carries `gbp_location_id`, and `location_daily_kpis.csv` maps one-to-one onto the Performance API's daily metrics.
- 2026-09-12: Built the FastAPI foundation — auth, organizations, memberships, migrations — and adapted the frontend template into a branded application shell.
- 2026-09-12: Brand pass on the frontend — favicon wired to `public/brand/favicon.webp`, maroon `#44131B` auth panel, sidebar collapsed by default with hover-to-expand showing the favicon collapsed and the full logo expanded. Fixed a Turbopack root-resolution failure caused by an unrelated `package-lock.json` in the user's home directory, by pinning `turbopack.root` in `next.config.ts`.
- 2026-09-12: **Scope redirected** from the recommendation engine to the GBP management platform. Verified the current API surface against live documentation: reviews and replies remain v4-only, `readMask`/`updateMask` are mandatory, Q&A was discontinued in November 2025.
- 2026-09-12: Backend data foundation landed and verified. Models and schemas restructured into packages; 11 new tables; `users.password_hash` made nullable for Google-only accounts. Dropped `google-auth` in favour of PyJWT + JWKS for ID-token verification, avoiding a second HTTP stack.
- 2026-09-12: Google OAuth primitives written (`app/services/google/oauth.py`). Note: `offline=True` forces `prompt=consent` because Google returns a refresh token only on fresh consent — without it the stored connection silently dies with its first access token.
