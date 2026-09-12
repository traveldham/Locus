# Status

Last updated: 2026-09-12

## Board

| # | Task | Status |
|---|---|---|
| 001 | Backend data foundation | ✅ DONE |
| 002 | Google sign-in + onboarding API | ✅ BUILT |
| 003 | GBP connect, providers, discovery, import | ✅ BUILT |
| 004 | Projects + Locations API | ✅ BUILT |
| 005 | Auth + onboarding UI | ✅ BUILT |
| 006 | Integrations + discovery wizard UI | ✅ BUILT |
| 007 | Projects + Locations UI | ✅ BUILT |
| 008 | Router wiring + verification | ✅ DONE |
| 009 | Sync engine (arq, optional Redis) | ✅ BUILT |
| 010 | Profile write path: preview, apply, audit | ✅ BUILT |
| 011 | Reviews: model, v4 provider, reply API | ✅ BUILT |
| 012 | Dark mode fix (was never working) | ✅ FIXED |
| 013 | Posts / Media / Bulk ops | ⬜ NEXT |

`BUILT` not `DONE`: the code exists and its checks pass, but **none of it has been run against a live system**. No server has been started, no migration applied, nothing opened in a browser. That is the gap.

## Verification as of this pass

| Check | Result |
|---|---|
| Backend tests | **64 passed** |
| `ruff check` / `format --check` | clean, 68 files |
| Frontend `tsc --noEmit` | clean |
| Frontend `npm run lint` | clean |
| Registered endpoints | **35**, no duplicates |
| Migration chain | linear, single head `20260913_0003` |
| Stray `dark:` misuse | none |

## What exists

**35 endpoints** — auth (7, incl. Google sign-in), onboarding (1), integrations (6), projects (6), locations (5, incl. edit preview/apply/audit), reviews (5), sync (3), health (1), plus docs.

**12 frontend routes** — login · register · auth/callback · onboarding · dashboard · projects · projects/[id] · locations · locations/[id] · reviews · settings/integrations · settings/integrations/discover.

The full loop runs on the **fixture provider** (your 12 sample clinics): sign in → connect → discover → import → browse → **edit a profile with preview and audit** → **reply to reviews**. `GBP_PROVIDER=live` is the only change when Google approves.

## Blocked — all on the user

| Blocker | Effect |
|---|---|
| GBP API access not applied for | Live Google calls fail (0 QPM). ~2 week review. |
| OAuth redirect URIs not registered | Real consent round-trip untestable. |
| Migration never applied | `alembic upgrade head` is an unexercised path. |
| Never opened in a browser | No visual pass; dark mode in particular has **never once rendered correctly** before task 012. |

See `PENDING.md` for the exact steps.

## Next

**013 — Posts, Media, Bulk operations.** All buildable on fixtures without Google approval. Bulk ops are what justify a multi-location product, and must pace against the 10-edits-per-minute-per-profile cap.
