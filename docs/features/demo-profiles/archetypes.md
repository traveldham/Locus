# The ten archetypes

Declared in `backend/generator_data/archetypes.py`. An archetype is two things: an **identity**
(name, trade, city, the words customers write about it) and a **`Problems`** record — a
declaration of which checks the generated data should fail.

Every field on `Problems` defaults to healthy, so an archetype states only its own faults and
reads as a short diagnosis.

## The spread

Deliberate. One profile's reputation is the disaster, one's visibility has collapsed, one is
operationally broken, one has no content, and the rest mix.

| Key | Business | Category | City | The story |
| --- | --- | --- | --- | --- |
| `riverside-grill` | Riverside Grill | Restaurant | Austin, TX | Rating down to 2.7, 40+ complaints unanswered, no hours posted |
| `ironclad-strength` | Ironclad Strength Gym Denver | Gym | Denver, CO | Invisible on every local search, including its own name |
| `maison-noir-salon` | Maison Noir Hair Studio | Hair salon | Portland, OR | Three photos, nothing ever posted, open two weekdays on paper |
| `carter-auto-works` | Carter Auto Works | Auto repair shop | Phoenix, AZ | 18 booking requests never answered and a third of visits lost |
| `brightsmile-family-dental` | Brightsmile Family Dental | Dental clinic | Tampa, FL | Unverified listing, contradictory services, complaints unanswered |
| `paws-and-claws-vet` | Paws & Claws Veterinary Clinic | Veterinarian | Nashville, TN | Impressions down by half, four days nobody called or clicked |
| `bluebird-coffee` | Bluebird Coffee House | Coffee shop | Seattle, WA | Five photos, nothing posted since spring, slipping out of the map pack |
| `greenleaf-pharmacy` | Greenleaf Community Pharmacy | Pharmacy | Columbus, OH | No phone, no website, no description, and an unverified listing |
| `hartley-law` | Hartley & Boyd Law Offices | Law firm | Chicago, IL | Nowhere near the map pack, 46 reviews against rivals' 420 |
| `rapid-flow-plumbing` | Rapid Flow Plumbing | Plumber | Kansas City, MO | Emergency calls unanswered, a third of visits missed, calls down half |

Ten distinct industries, ten distinct Google categories, and **none of them is `Dentist`** —
so no archetype's attribute catalog can collide with the seeded clinics'.

## What makes them read as real businesses

Each archetype carries its own written material, not templated filler:

- **6 complaints, 3 mixed and 4 positive review lines**, industry-specific and concrete
  ("Booked a correction, left with two different colours and a burnt hairline"), cycled with
  a seeded RNG and matched to the star rating.
- **Its own services, search terms, booking services, keywords and named rivals.**
- **Three post summaries** in the trade's own voice.
- **Category-specific attributes** on top of a shared base catalog — a restaurant gets
  `serves_beer`, `outdoor_seating`, `accepts_reservations`; a vet gets `in_house_laboratory`,
  `cat_only_waiting_area`.

## The `Problems` record

Roughly fifty knobs across the six categories. A sample:

```python
Problems(
    # profile
    verified=False, phone=False, website=None, description="missing",
    open_days=("WEDNESDAY", "THURSDAY"), odd_hours=True,
    attribute_share=0.15, accessibility_answered=False,
    # reputation — star mix as counts of 1..5 stars, per 90-day window
    recent_mix=(18, 10, 5, 2, 2), prior_mix=(4, 3, 5, 7, 12),
    reply_share=0.12, critical_reply_share=0.05, reply_delay_days=21,
    competitor_reviews=320,
    # visibility — (keyword, intent, rank pattern)
    keyword_plan=(("riverside grill", "general", "gone"), …), losing_terms=2,
    # operations
    bookings=BookingMix(new_stale=16, expired=10, confirmed=2,
                        completed=6, cancelled=7, no_show=5),
    weekend_requests=10, google_bookings_zero=True, lead_collapse=True,
    # performance
    impressions_base=260, impressions_drop=0.39, calls_drop=0.52,
    zero_action_streak=3, missing_days=3,
    # content
    photos=4, photo_types=(0, 0, 0), videos=0, photo_age_days=214,
    post_types=(),                      # never posted at all
)
```

### Rank patterns

A keyword's eight weekly checks are declared by name, so one keyword can fail several checks
at once:

| Pattern | Positions, oldest week first | Triggers |
| --- | --- | --- |
| `top` | 1,1,1,1,1,1,1,1 | nothing — a healthy control |
| `pack` | 2,2,3,2,3,2,2,3 | in the pack throughout |
| `near` | 6,5,7,6,5,6,7,6 | `near_pack_opportunity` |
| `mid` | 11,12,10,13,11,12,11,12 | `pack_share_low` |
| `lost` | 2,3,2,3,2,3,2,**8** | `pack_lost` + `rank_dropped` |
| `slip` | 2,2,3,2,3,6,9,**14** | `pack_lost` + `rank_dropped`, harder |
| `drop` | 5,6,5,6,5,6,5,**12** | `rank_dropped` |
| `gone` | not found, every week | `not_found_persistent` (+ `branded_not_first` if branded) |

## The `failing` field

Each archetype declares which categories it exists to drag down. That is **not** simply its
two lowest scores: reputation and performance bottom out easily under the scoring policy,
while a notice-heavy category like visibility never falls far however badly it does. The field
records the *story*, and a test asserts each declared category actually scores ≤75.

## Adding an eleventh

1. Append an `Archetype` to `ARCHETYPES` with its identity, copy and a `Problems` record.
2. `uv run python -m generator_data --verify --rules <key>` and read which checks fired and
   which abstained.
3. Adjust until the intended ones are `triggered` rather than `insufficient_data`.
4. Add it to `INTENDED` in `tests/test_demo_profiles.py` if it should be guarded.

The module asserts at import that the keys, industries and categories are all distinct.
