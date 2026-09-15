# The generator

`backend/generator_data/` — a standalone package that turns an archetype into thousands of
internally consistent rows and writes them through the models.

```
archetypes.py   the ten businesses + their Problems records
generator.py    Archetype + reference date  →  ProfileData (rows as plain dicts)
snapshot.py     ProfileData  →  the audit engine's snapshot, no database needed
importer.py     ProfileData  →  the database, through app/models, idempotently
verify.py       run the real six workers over every archetype, print the scores
__main__.py     the CLI
```

## Determinism

Everything derives from one seeded `random.Random(f"{key}:{reference}")` and one reference
date, so the same archetype on the same date produces byte-identical data. That is what makes
the tests stable and the demo reproducible.

Rows are emitted as plain dicts of **model keyword arguments** — real `date`, `datetime`,
`int` and `None` values, never strings pretending to be numbers. The importer hands them to
SQLAlchemy; `snapshot.py` converts the same dicts to the shape the engine reads. Both paths
see exactly the same data, and a test asserts the two produce identical scores.

## Clearing the evidence gates

The generator's one job is that the data must be present and bad. Every series is sized to
clear the gate of the check it is meant to fail:

| Series | Sized for |
| --- | --- |
| 46-71 reviews across two 90-day windows | `min_reviews` (5) in both, so the rating **and** its trend are judged |
| Replies on the **oldest** reviews first | A 21-day median delay needs a review at least 21 days old to sit on |
| 36-41 bookings over 90 days | `booking_min_requests` (10) decidable **and** `booking_min_settled` (10) settled |
| 108-112 daily performance rows | 28-day current + 28-day previous window, ≥70% weekday-paired |
| 8 weekly rank checks per keyword | `not_found_min_weeks` (4) consecutive, `rank_trend_weeks` (4) of trend |
| 6 months of search terms | An exact pair of complete months above the 200-impression floor |
| 3 rivals per keyword-week | `rival_min_keywords_ahead` (3) with a measurable profile gap |

Star ratings come from an explicit distribution — `recent_mix=(18,10,5,2,2)` is eighteen
1-stars, ten 2-stars and so on — so the mean is a stated fact rather than an emergent one, and
the recent/prior split makes `rating_trend_falling` provable.

## Things the engine taught the generator

Each of these was found by running the real workers and reading what came back
`insufficient_data`:

1. **Notices barely cost anything.** Severity penalties are critical 1.0, warning 0.6, notice
   0.25. A category made mostly of notices cannot fall far, so overall scores below 50 need
   *every* category bad, not two.
2. **Several checks cross into "warning" only past a second threshold.** Search terms must
   lose **86%**, not 50%, before `search_term_losing` stops being a notice; weekday gaps need
   3+ days; call and click declines need ≥50% to go critical; impressions need ≥37%.
3. **`branded_not_first` (weight 3) abstains** unless a tracked keyword shares a distinctive
   word with the stored name — so every keyword plan now carries a branded keyword.
4. **Missing performance days break zero-action streaks.** The gap offsets had to be moved
   clear of the streak, because a missing day is unknown and "no data" must never read as
   "nobody acted".
5. **The attribute top-up loop was answering accessibility attributes** for archetypes meant
   to leave them blank, so `accessibility_unanswered` came back `clear`. Found by the engine,
   fixed in the generator.

## Idempotence

`import_archetypes` reads which archetypes the organization already holds by scanning for
`google_location_name` beginning `locations/demo-`, then for each requested key:

- unknown key → reported in `unknown`, never raised
- already present → reported in `skipped`
- otherwise → generated and written

A second import of the same key writes nothing — not a duplicate profile, not a second copy of
its reviews. The test asserts the exact review count is unchanged.

## Verifying

```bash
uv run python -m generator_data --verify --reference 2026-09-14
```

Generates each archetype, builds its snapshot and runs `analyze()` — the real six workers —
printing score, grade, coverage, finding count and all six category scores. `--rules <key>`
lists every check that triggered and every one that abstained for one profile.

This is the honest test: running the real workers is the only way to know the data is bad in
the way the engine *measures*, rather than merely thin.

## Tests

`backend/tests/test_demo_profiles.py`, 19 tests:

- the catalogue declares ten distinct businesses, none claiming `Dentist`
- generation is deterministic; a profile is over 400 rows
- import writes the profile and every related table, and joins a project
- **a second import of the same key is a no-op**
- an unknown key is reported without stopping the batch
- another organization sees none of it, and can import the same key cleanly
- **the real audit pipeline** (`run_job` — prepare, six workers, publish) over five
  archetypes asserts the score lands in its intended band with the intended rules
  `triggered`, never `insufficient_data`
- every archetype is scored and none comes back `not_evaluated`
- the four API endpoints, including tenant scoping and project linking
