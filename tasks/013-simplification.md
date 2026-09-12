# 013 — Simplification: remove the sync engine and all fixture data

**Status:** IN PROGRESS

## Why

Two things were built that turned out to be wrong for the actual situation.

### 1. The sync engine was solving a problem that does not exist

It exists to pace requests against Google's per-minute quota, through a queue, on a schedule.

The facts:
- This project's Google quota is **literally zero** — proven by a live call returning `429 RESOURCE_EXHAUSTED` with `"quota_limit_value": "0"`.
- The owner manages **one business**, not hundreds of locations.

So it was a token-bucket rate limiter pacing against nothing, feeding a queue that never had contention, on a schedule that needed a Redis nobody had installed. ~800 lines and two dependencies for a problem that will not arrive at this scale.

### 2. Fixture data confused a real user in a real way

Connecting a genuine Google account surfaced "Brightpath Dental Group" — sample dental clinics from the take-home CSVs. The owner reasonably read that as the product inventing data about their business.

Fake data in a shipped product is a correctness problem, not a convenience. It belongs in tests, where it cannot be mistaken for the truth.

## What went

| Removed | Approx. lines |
|---|---|
| `app/services/sync/` — worker, runner, pacing, job registry | 800 |
| `app/api/sync.py`, `app/schemas/sync.py`, `tests/test_sync.py` | — |
| `arq` and `redis` dependencies, `REDIS_URL`, `SYNC_CALLS_PER_MINUTE` | — |
| `app/services/providers/fixture.py` and `FixtureReviewsProvider` | 320 |
| `GBP_PROVIDER` setting and the whole fixture/live branch | — |
| The fixture-connection shortcut in `ensure_connection` | — |

## What stayed, and why

- **`live.py`, the reviews provider, `google/client.py`** — this is the product. It returns 403/429 today because the project is unapproved, which is a permission state, not dead code. Delete it and the app can never do anything.
- **The `SyncRun` table** — it records what each refresh did and what failed. That is bookkeeping and it is how errors surface in the UI. Only the engine around it went.
- **The work itself** — anything that used to be queued is now simply called directly. For one business, a direct fetch is entirely adequate.

## Replacing fixtures in tests

Around 30 of the 64 tests depended on the fixture provider, and `conftest.py` pinned `gbp_provider="fixture"` for the whole suite.

Replaced with a small in-memory stub defined inside the test tree and injected by dependency override. Tests keep a fake; the application no longer has one. Tests still never touch the network.

## The lesson worth keeping

**The blocker should have been tested on day one.** One API call — thirty seconds — would have returned `quota: 0` and reframed everything before a queue, a worker and a rate limiter were written for data that cannot arrive.

Instead the constraint was written into documents repeatedly and treated as understood, while building continued past it. Documenting a risk is not the same as testing it.

Next time: if a project depends on third-party access, **make the smallest real call first**, before designing anything around it.

## Also worth remembering

An architectural guess is cheap to reverse when it is isolated. The queue was removable in one task precisely because `enqueue()` was the only place that knew how jobs ran. Concentrating a guess behind one seam is what made deleting it a contained change rather than a rewrite.
