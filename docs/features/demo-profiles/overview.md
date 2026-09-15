# Demo profiles

Ten deliberately poor-quality businesses across ten industries, generated on demand, so the
audit has something to find.

Code: `backend/generator_data/` (a standalone package), API `backend/app/api/demo_profiles.py`.

## The problem it solves

The seeded demo world is twelve dental clinics from the assignment dataset, and they are
mostly **healthy** — the flagship scores 81/100, "good". That demos badly: the audit finds
little, so the suggestion layer and the agent have almost nothing to do.

## The constraint that shapes everything

**Missing data does not produce a low score.** `scoring.py` excludes unevaluated checks from
the denominator: a check without enough evidence returns `insufficient_data` and is skipped,
never counted as a failure. A profile with sparse data reports low coverage and a
`not_evaluated` grade — which demos *worse* than what already exists.

So the generated data has to be **present and bad**, and it has to clear each check's
minimum-evidence gate before failing it. Three reviews produce `insufficient_data`; thirty
reviews averaging 2.1 stars produce a critical finding. That is why each profile carries
500-600 rows across thirteen tables rather than a thin sketch.

## What the ten score

Audited with the real six-worker pipeline, reference date 2026-09-14:

| Key | Industry | Headline categories | Score | Grade | Findings |
| --- | --- | --- | --- | --- | --- |
| `greenleaf-pharmacy` | Pharmacy, Columbus | profile 51, content 32 | **46** | poor | 95 |
| `riverside-grill` | Restaurant, Austin | reputation 37, content 32 | **49** | poor | 92 |
| `ironclad-strength` | Gym, Denver | visibility 54, profile 59 | **49** | poor | 104 |
| `maison-noir-salon` | Hair salon, Portland | content 32, reputation 39 | **52** | fair | 89 |
| `carter-auto-works` | Auto repair, Phoenix | operations 58, reputation 38 | **58** | fair | 92 |
| `brightsmile-family-dental` | Dental, Tampa | profile 72, reputation 44 | **58** | fair | 91 |
| `paws-and-claws-vet` | Veterinary, Nashville | performance 24, operations 61 | **60** | fair | 89 |
| `rapid-flow-plumbing` | Plumber, Kansas City | operations 60, performance 52 | **64** | fair | 82 |
| `hartley-law` | Law firm, Chicago | visibility 62, reputation 46 | **66** | fair | 70 |
| `bluebird-coffee` | Coffee shop, Seattle | content 48, reputation 62 | **70** | fair | 68 |

42-60 of the 67 checks fire on each, at coverage 0.82-0.97. Compare the flagship seeded
clinic: 81/100 with few findings.

## Using it

**From the UI** — Profiles → *Import sample profiles* → tick → Import. Then run an audit on
any of them.

**From the command line:**

```bash
uv run python -m generator_data --list
uv run python -m generator_data --verify [--rules riverside-grill]
uv run python -m generator_data                       # all ten into the only/first org
uv run python -m generator_data --keys riverside-grill --project "Brightpath Dental Group"
```

Importing never runs an audit — that is the user's next, separate step.

## How imported rows are marked

Using what already exists, not a parallel flag:

- **`Location.source = LocationSource.fixture`**, and the natural key
  `google_location_name = "locations/demo-<key>"`. The existing unique constraint on
  `(organization_id, google_location_name)` **is** the idempotence mechanism — a second import
  finds the row and skips it.
- Every analytics row is written **`DataSource.locus`**, including performance, search terms,
  media and posts, which the CSV loader marks `google`. These numbers were fabricated here;
  `google` would be a lie.
- Each archetype ships **its own attribute catalog under its own Google category**
  (`Dental clinic`, `Gym`, …, never `Dentist`), so the twelve seeded clinics' attribute
  coverage and competitor medians are untouched.

## Related

- [archetypes.md](archetypes.md) — the ten businesses and what is wrong with each
- [generator.md](generator.md) — how the rows are produced
- [api.md](api.md) — the two endpoints
- [../audit-engine/scoring.md](../audit-engine/scoring.md) — why "present and bad" is the requirement
