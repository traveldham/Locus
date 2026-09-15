"""Turn an archetype into thousands of internally consistent rows.

Everything is derived from one seeded `random.Random` and one reference date, so the
same archetype and the same date always produce byte-identical data. That is what makes
the tests stable and the demo reproducible.

Rows are emitted as plain dicts of model keyword arguments — real `date`, `datetime`,
`int` and `None` values, never strings pretending to be numbers. `importer.py` hands
them to the SQLAlchemy models and `snapshot.py` converts them to the shape the audit
engine reads, so both paths see exactly the same data.

The generator's one job is that the data must be **present and bad**. Every series is
sized to clear the minimum-evidence gate of the check it is meant to fail: enough rated
reviews in the rating window, enough settled visits to compute a no-show rate, enough
weekday-paired days to compare two performance windows, enough consecutive weekly rank
checks to call a keyword lost.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from generator_data.archetypes import BASE_ATTRIBUTES, Archetype

# ---- shared copy ---------------------------------------------------------------------

# A description that is long enough to be judged but says nothing: it names no trade, no
# city and no service, so `description_quality` fires while `description_short` does not.
THIN_DESCRIPTION = (
    "We have been proud to look after this community for many years, and our team is "
    "committed to everyone who walks through the door. Quality, value and a friendly "
    "welcome have always been the promise here, and we work hard to keep it that way "
    "every single day of the week, all year round. Come and see us."
)

WEEKDAY_NAMES = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)

# Positions for each rank pattern, oldest week first over `RANK_WEEKS` weekly checks.
# `None` is "not found", which is a state, never a position.
RANK_WEEKS = 8
RANK_PATTERNS: dict[str, tuple[int | None, ...]] = {
    "top": (1, 1, 1, 1, 1, 1, 1, 1),
    "pack": (2, 2, 3, 2, 3, 2, 2, 3),
    "near": (6, 5, 7, 6, 5, 6, 7, 6),
    "mid": (11, 12, 10, 13, 11, 12, 11, 12),
    "lost": (2, 3, 2, 3, 2, 3, 2, 8),
    "slip": (2, 2, 3, 2, 3, 6, 9, 14),
    "drop": (5, 6, 5, 6, 5, 6, 5, 12),
    "gone": (None, None, None, None, None, None, None, None),
}

POST_CTAS = ("book", "call", "learn_more", "sign_up", "get_offer")
BOOKING_CHANNELS = ("website", "google_profile", "phone", "walk_in")

PERFORMANCE_DAYS = 112  # four windows of history, so the card has a trend to draw
SEARCH_TERM_MONTHS = 6


@dataclass
class ProfileData:
    """One demo business, as rows. `keyword_ref` links ranks and rivals to a keyword."""

    key: str
    archetype: Archetype
    reference: date
    location: dict = field(default_factory=dict)
    project: dict = field(default_factory=dict)
    categories: list[dict] = field(default_factory=list)
    hours: list[dict] = field(default_factory=list)
    attributes: list[dict] = field(default_factory=list)
    catalog: list[dict] = field(default_factory=list)
    reviews: list[dict] = field(default_factory=list)
    performance: list[dict] = field(default_factory=list)
    search_terms: list[dict] = field(default_factory=list)
    media: dict | None = None
    posts: list[dict] = field(default_factory=list)
    bookings: list[dict] = field(default_factory=list)
    keywords: list[dict] = field(default_factory=list)
    ranks: list[dict] = field(default_factory=list)
    competitors: list[dict] = field(default_factory=list)

    @property
    def row_counts(self) -> dict[str, int]:
        return {
            "categories": len(self.categories),
            "hours": len(self.hours),
            "attributes": len(self.attributes),
            "catalog": len(self.catalog),
            "reviews": len(self.reviews),
            "performance": len(self.performance),
            "search_terms": len(self.search_terms),
            "media": 1 if self.media else 0,
            "posts": len(self.posts),
            "bookings": len(self.bookings),
            "keywords": len(self.keywords),
            "ranks": len(self.ranks),
            "competitors": len(self.competitors),
        }

    @property
    def total_rows(self) -> int:
        return 1 + 1 + sum(self.row_counts.values())


# ---- helpers -------------------------------------------------------------------------


def slug(value: str) -> str:
    out = "".join(c if c.isalnum() else "-" for c in value.lower())
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def at(reference: date, days_ago: int, hour: int = 12, minute: int = 0) -> datetime:
    """A timezone-aware instant that many days before the reference date."""
    moment = reference - timedelta(days=days_ago)
    return datetime(moment.year, moment.month, moment.day, hour, minute, tzinfo=UTC)


def month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def month_before(value: str) -> str:
    year, month = int(value[:4]), int(value[5:7])
    return f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"


def latest_monday(reference: date) -> date:
    return reference - timedelta(days=reference.weekday())


def spread(rng: random.Random, count: int, low: int, high: int) -> list[int]:
    """`count` day offsets spread across [low, high], newest first, always distinct-ish."""
    if count <= 0:
        return []
    if high <= low:
        return [low] * count
    step = (high - low) / count
    return [min(high, int(low + step * i + rng.random() * step)) for i in range(count)]


# ---- the generator -------------------------------------------------------------------


def generate(archetype: Archetype, reference: date | None = None) -> ProfileData:
    """Every row for one demo business. Deterministic for a given archetype and date."""
    reference = reference or date.today()
    rng = random.Random(f"{archetype.key}:{reference.isoformat()}")
    data = ProfileData(key=archetype.key, archetype=archetype, reference=reference)

    _catalog(data)
    _location(data)
    _project(data)
    _categories(data)
    _hours(data)
    _attributes(data)
    _reviews(data, rng)
    _keywords_and_ranks(data, rng)
    _search_terms(data, rng)
    _performance(data, rng)
    _media(data)
    _posts(data, rng)
    _bookings(data, rng)
    return data


# ---- profile -------------------------------------------------------------------------


def _description(archetype: Archetype) -> str | None:
    """The stored description, in whichever of the six shapes the archetype declares."""
    problems = archetype.problems
    category, city = archetype.primary_category, archetype.city
    match problems.description:
        case "missing":
            return None
        case "short":
            return f"{category} in {city}, {archetype.state}."
        case "thin":
            return THIN_DESCRIPTION
        case "stuffed":
            # The category and the city five times each: over `description_max_term_repeats`.
            line = (
                f"Looking for a {category.lower()} in {city}? This {category.lower()} is the "
                f"{category.lower()} {city} trusts. Best {category.lower()} in {city}, top rated "
                f"{category.lower()} near {city}, and the {city} {category.lower()} locals "
                f"recommend. Book the {city} {category.lower()} today and see why {city} keeps "
                "coming back."
            )
            return line
        case "long":
            filler = (
                " Every member of the team is trained in-house, every quote is confirmed in "
                "writing before any work starts, and every client keeps a named point of "
                "contact for the life of the matter, which we have found removes most of the "
                "friction that people expect from a practice of this kind."
            )
            text = archetype.description
            while len(text) <= 750:
                text += filler
            return text
        case _:
            return archetype.description


def _location(data: ProfileData) -> None:
    archetype, problems = data.archetype, data.archetype.problems
    website = {
        "https": archetype.website,
        "http": archetype.website.replace("https://", "http://") if archetype.website else None,
        None: None,
    }[problems.website]
    data.location = {
        "google_location_name": f"locations/demo-{archetype.key}",
        "source_location_id": f"DEMO-{archetype.key.upper()}",
        "google_resource_name": f"accounts/demo/locations/demo-{archetype.key}",
        "place_id": f"demo-place-{archetype.key}",
        "store_code": f"DEMO-{archetype.key[:24].upper()}",
        "title": archetype.name,
        "primary_category_name": f"gcid:{slug(archetype.primary_category).replace('-', '_')}",
        "primary_category_display": archetype.primary_category,
        "address_lines": [f"{100 + len(archetype.key)} Main Street"],
        "locality": archetype.city,
        "administrative_area": archetype.state if problems.address_complete else None,
        "postal_code": archetype.postal_code if problems.address_complete else None,
        "region_code": "US",
        "latitude": archetype.latitude if problems.pin else None,
        "longitude": archetype.longitude if problems.pin else None,
        "phone_primary": archetype.phone if problems.phone else None,
        "website_uri": website,
        "description": _description(archetype),
        "open_status": "closed_temporarily" if problems.temporarily_closed else "open",
        "opening_date": (
            date(2014 + len(archetype.key) % 8, 3, 11) if problems.opening_date else None
        ),
        "has_voice_of_merchant": problems.verified,
        "has_pending_edits": not problems.verified,
        "has_google_updated": False,
        "is_duplicate": False,
        "maps_uri": f"https://maps.google.com/?cid=demo-{archetype.key}",
        "new_review_uri": f"https://search.google.com/local/writereview?placeid=demo-{archetype.key}",
    }


def _project(data: ProfileData) -> None:
    archetype = data.archetype
    data.project = {
        "name": archetype.name,
        "slug": f"demo-{archetype.key}",
        "website_url": archetype.website or None,
        "description": archetype.description or None,
        "services": list(archetype.services),
    }


def _categories(data: ProfileData) -> None:
    archetype, problems = data.archetype, data.archetype.problems
    data.categories = [
        {
            "category_name": f"gcid:{slug(archetype.primary_category).replace('-', '_')}",
            "display_name": archetype.primary_category,
            "is_primary": True,
        }
    ]
    for name in archetype.extra_categories[: problems.additional_categories]:
        data.categories.append(
            {
                "category_name": f"gcid:{slug(name).replace('-', '_')}",
                "display_name": name,
                "is_primary": False,
            }
        )


def _hours(data: ProfileData) -> None:
    problems = data.archetype.problems
    for index, day_name in enumerate(WEEKDAY_NAMES):
        if day_name not in problems.open_days:
            continue
        # One deliberately impossible period: ninety minutes is not an opening day.
        odd = problems.odd_hours and index == min(
            WEEKDAY_NAMES.index(d) for d in problems.open_days
        )
        data.hours.append(
            {
                "hours_type": "REGULAR",
                "open_day": day_name,
                "open_hour": 9,
                "open_minute": 0,
                "close_day": day_name,
                "close_hour": 10 if odd else 17,
                "close_minute": 30,
            }
        )


def _catalog(data: ProfileData) -> None:
    """This archetype's own attribute vocabulary.

    Keyed on its own primary category, so it never merges with — or shifts the attribute
    coverage of — the dental catalog the original sample dataset ships.
    """
    archetype = data.archetype
    category = archetype.primary_category
    for name, group in (*BASE_ATTRIBUTES, *archetype.attributes):
        data.catalog.append(
            {
                "external_attribute_id": f"demo-{slug(category)}-{name}",
                "attribute_name": name,
                "attribute_group": group,
                "applies_to_category": category,
                "value_type": "bool",
            }
        )


def _attributes(data: ProfileData) -> None:
    """Answer a share of the catalog, honouring the archetype's declared gaps."""
    problems = data.archetype.problems
    names = [row["attribute_name"] for row in data.catalog]
    accessibility = [
        row["attribute_name"] for row in data.catalog if row["attribute_group"] == "accessibility"
    ]
    answered: dict[str, bool] = {}

    if problems.accessibility_answered:
        for name in accessibility:
            answered[name] = True
    # A business that takes weekend requests claims Saturday appointments, whether or not
    # it actually posts Saturday hours — which is the contradiction the audit looks for.
    if problems.weekend_requests and "saturday_appointments" in names:
        answered["saturday_appointments"] = True
    for name in problems.attributes_denied:
        if name in names:
            answered[name] = False

    # An archetype that leaves accessibility unanswered must never have it topped up:
    # `accessibility_unanswered` is the check it is meant to fail.
    candidates = [
        name
        for name in names
        if problems.accessibility_answered or name not in accessibility
    ]
    target = round(problems.attribute_share * len(names))
    for name in candidates:
        if len(answered) >= target:
            break
        answered.setdefault(name, True)

    for name in names:
        if name not in answered:
            continue
        data.attributes.append(
            {
                "attribute_id": f"attributes/{name}",
                "value_type": "BOOL",
                "values": [answered[name]],
            }
        )


# ---- reputation ----------------------------------------------------------------------


def _stars_from_mix(mix: tuple[int, int, int, int, int]) -> list[int]:
    return [star for star, count in enumerate(mix, start=1) for _ in range(count)]


def _comment(archetype: Archetype, star: int, rng: random.Random) -> str:
    if star <= 2:
        return rng.choice(archetype.complaints)
    if star == 3:
        return rng.choice(archetype.mixed)
    return rng.choice(archetype.praise)


def _reviews(data: ProfileData, rng: random.Random) -> None:
    archetype, problems = data.archetype, data.archetype.problems
    reference = data.reference

    recent = _stars_from_mix(problems.recent_mix)
    prior = _stars_from_mix(problems.prior_mix)
    rng.shuffle(recent)
    rng.shuffle(prior)

    # Recent reviews live in the 90-day rating window; the split controls review velocity.
    last_30 = min(problems.recent_last_30, len(recent))
    ages = spread(rng, last_30, problems.newest_review_days, 29)
    ages += spread(rng, len(recent) - last_30, 30, 89)
    ages += spread(rng, len(prior), 90, 179)
    stars = recent + prior
    if ages:
        ages[0] = problems.newest_review_days  # the newest review is exactly where declared

    rows = []
    for index, (star, days_ago) in enumerate(zip(stars, ages, strict=True)):
        created = at(reference, days_ago, hour=9 + index % 10, minute=(index * 7) % 60)
        rows.append(
            {
                "google_review_id": f"demo-{archetype.key}-review-{index:03d}",
                "google_review_name": (
                    f"accounts/demo/locations/demo-{archetype.key}/reviews/{index:03d}"
                ),
                "reviewer_display_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_INITIALS)}.",
                "reviewer_photo_url": None,
                "is_anonymous": False,
                "star_rating": star,
                "comment": _comment(archetype, star, rng),
                "create_time": created,
                "update_time": created,
                "reply_comment": None,
                "reply_update_time": None,
                "_days_ago": days_ago,
            }
        )

    _replies(data, rows, rng)
    for row in rows:
        row.pop("_days_ago")
    data.reviews = rows


def _replies(data: ProfileData, rows: list[dict], rng: random.Random) -> None:
    """Answer the declared share of reviews, oldest first, with the declared delay.

    Replying to the oldest first is both realistic and necessary: a reply can never be
    dated after the analysis date, so a fourteen-day delay needs a review at least
    fourteen days old to sit on.
    """
    problems = data.archetype.problems
    delay = problems.reply_delay_days
    order = sorted(range(len(rows)), key=lambda i: -rows[i]["_days_ago"])
    critical = {i for i in order if rows[i]["star_rating"] <= 3}

    want_critical = round(problems.critical_reply_share * len(critical))
    want_total = round(problems.reply_share * len(rows))
    chosen: list[int] = [i for i in order if i in critical][:want_critical]
    for index in order:
        if len(chosen) >= want_total:
            break
        if index not in critical:
            chosen.append(index)

    offsets = (-2, -1, 0, 0, 1, 2)
    for position, index in enumerate(chosen):
        row = rows[index]
        # Clamp so a reply is never dated after the analysis date.
        wait = max(0, min(delay + offsets[position % len(offsets)], row["_days_ago"]))
        row["reply_comment"] = rng.choice(REPLY_TEMPLATES)
        row["reply_update_time"] = row["create_time"] + timedelta(days=wait, hours=2)


FIRST_NAMES = (
    "Alex", "Priya", "Marcus", "Dana", "Tomas", "Ruth", "Kelvin", "Nadia", "Owen", "Farrah",
    "Hugo", "Leila", "Sean", "Maya", "Caleb", "Ines", "Jonah", "Tessa", "Andre", "Bethan",
)
LAST_INITIALS = ("A", "B", "C", "D", "F", "G", "H", "K", "L", "M", "N", "P", "R", "S", "T", "W")
REPLY_TEMPLATES = (
    "Thank you for taking the time to write this. We would like to put it right — please "
    "ask for the manager on your next visit.",
    "We appreciate the feedback and we are sorry this was your experience. The team has "
    "been briefed and we are making changes.",
    "Thanks for letting us know. This is not the standard we hold ourselves to and we are "
    "looking into what happened.",
    "Thank you — we are glad it went well and we hope to see you again soon.",
)


# ---- visibility ----------------------------------------------------------------------


def _keywords_and_ranks(data: ProfileData, rng: random.Random) -> None:
    archetype, problems = data.archetype, data.archetype.problems
    plan = problems.keyword_plan or tuple(
        (term, "general", "mid") for term in archetype.search_terms[:5]
    )
    monday = latest_monday(data.reference)
    weeks = [monday - timedelta(weeks=RANK_WEEKS - 1 - i) for i in range(RANK_WEEKS)]

    for index, (keyword, intent, pattern) in enumerate(plan):
        ref = f"demo-{archetype.key}-kw-{index:02d}"
        data.keywords.append(
            {
                "external_keyword_id": ref,
                "keyword": keyword,
                "search_intent": intent,
                "device": "mobile" if index % 2 else "desktop",
                "tracking_started_on": monday - timedelta(weeks=RANK_WEEKS + 6),
            }
        )
        positions = RANK_PATTERNS[pattern]
        for week, position in zip(weeks, positions, strict=True):
            data.ranks.append(
                {
                    "keyword_ref": ref,
                    "week_start": week,
                    "rank_absolute": position,
                    "rank_in_local_pack": position if position and position <= 3 else None,
                    "found": position is not None,
                    "result_url": archetype.website or None,
                }
            )
            _rivals(data, ref, week, position, rng)


def _rivals(
    data: ProfileData, ref: str, week: date, position: int | None, rng: random.Random
) -> None:
    """Three rivals per keyword-week, every one of them ranking ahead of us.

    Their profile figures are scaled from our own so the comparison the visibility worker
    makes — reviews, rating, photos inside the same keyword and week — actually resolves.
    """
    archetype, problems = data.archetype, data.archetype.problems
    our_rating = _mean_stars(problems)
    factors = (0.8, 1.0, 1.3)
    for index, name in enumerate(archetype.rivals):
        ahead = max(1, (position - index - 1) if position else index + 1)
        data.competitors.append(
            {
                "keyword_ref": ref,
                "week_start": week,
                "competitor_name": name,
                "competitor_place_id": f"demo-rival-{slug(name)}",
                "rank_absolute": ahead,
                "review_count": max(
                    1, round(problems.competitor_reviews * factors[index] + rng.randint(-4, 4))
                ),
                "average_rating": round(min(4.9, our_rating + 0.8 + index * 0.1), 1),
                "photo_count": max(1, round(problems.photos * problems.rival_strength) + index * 6),
                "is_claimed": True,
            }
        )


def _mean_stars(problems) -> float:
    stars = _stars_from_mix(problems.recent_mix) + _stars_from_mix(problems.prior_mix)
    return sum(stars) / len(stars) if stars else 3.0


def _search_terms(data: ProfileData, rng: random.Random) -> None:
    """Monthly search terms ending at the latest complete month before the reference date.

    The visibility worker only ever pairs two exact months, so both the latest complete
    month and the one before it must carry an exact count above the impressions floor for
    a losing term to be judged at all.
    """
    archetype, problems = data.archetype, data.archetype.problems
    first_of_month = data.reference.replace(day=1)
    latest = month_key(first_of_month - timedelta(days=1))
    months = [latest]
    for _ in range(SEARCH_TERM_MONTHS - 1):
        months.append(month_before(months[-1]))
    months.reverse()

    for index, term in enumerate(archetype.search_terms):
        losing = index < problems.losing_terms
        # Only a term above the impressions floor in the earlier month is ever paired, so
        # the long tail stays below it: Google truncates small terms and the worker knows
        # better than to judge them.
        base = (480 - index * 40) if losing else (185 - index * 16)
        for position, ym in enumerate(months):
            is_latest = ym == latest
            value = base + position * 12 + rng.randint(-15, 15)
            if losing and is_latest:
                value = round(base * 0.14)
            threshold = value < 60
            data.search_terms.append(
                {
                    "year_month": ym,
                    "search_term": term,
                    "impressions": 15 if threshold else max(20, value),
                    "is_threshold": threshold,
                }
            )


# ---- performance ---------------------------------------------------------------------

WEEKDAY_WEIGHT = (1.08, 1.05, 1.02, 1.0, 1.12, 0.84, 0.69)


def _performance(data: ProfileData, rng: random.Random) -> None:
    problems = data.archetype.problems
    end = data.reference - timedelta(days=1)  # windows end on the last day with data
    current_start = end - timedelta(days=27)
    previous_start = current_start - timedelta(days=28)

    # Gaps sit clear of the zero-action streak: a missing day breaks a streak, and
    # "nobody acted" and "nothing was reported" must stay different facts.
    missing = {end - timedelta(days=offset) for offset in (2, 17, 22, 26)[: problems.missing_days]}
    streak_days = {end - timedelta(days=8 + i) for i in range(problems.zero_action_streak)}

    for back in range(PERFORMANCE_DAYS):
        moment = end - timedelta(days=back)
        if moment in missing:
            continue
        in_current = moment >= current_start
        weight = WEEKDAY_WEIGHT[moment.weekday()]
        drop = problems.impressions_drop if in_current else 0.0
        impressions = max(12, round(problems.impressions_base * weight * (1 - drop)))
        maps_share = 0.55 + (problems.maps_shift if in_current else 0.0)
        mobile_share = 0.62 + (problems.mobile_shift if in_current else 0.0)

        maps = round(impressions * maps_share)
        search = impressions - maps
        row = {
            "date": moment,
            "impressions_maps_mobile": round(maps * mobile_share),
            "impressions_maps_desktop": maps - round(maps * mobile_share),
            "impressions_search_mobile": round(search * mobile_share),
            "impressions_search_desktop": search - round(search * mobile_share),
            "conversations": max(0, round(impressions * 0.012)),
            "bookings": 0 if problems.google_bookings_zero else max(0, round(impressions * 0.02)),
        }
        if moment in streak_days:
            row["call_clicks"] = 0
            row["direction_requests"] = 0
            row["website_clicks"] = 0
        else:
            base = problems.impressions_base * weight
            row["call_clicks"] = _action(base, 0.062, problems.calls_drop, in_current, rng)
            row["direction_requests"] = _action(
                base, 0.051, problems.directions_drop, in_current, rng
            )
            row["website_clicks"] = _action(base, 0.044, problems.clicks_drop, in_current, rng)
        data.performance.append(row)

    data.performance.sort(key=lambda r: r["date"])
    # Keep the previous window whole: a missing day there would drop its pair as well.
    assert all(
        any(r["date"] == previous_start + timedelta(days=i) for r in data.performance)
        for i in range(28)
    )


def _action(base: float, rate: float, drop: float, in_current: bool, rng: random.Random) -> int:
    value = base * rate * (1 - drop if in_current else 1.0)
    return max(0, round(value) + rng.randint(-1, 1))


# ---- content -------------------------------------------------------------------------


def _media(data: ProfileData) -> None:
    problems = data.archetype.problems
    interior, exterior, team = problems.photo_types
    data.media = {
        "photo_count": problems.photos,
        "interior_photo_count": interior,
        "exterior_photo_count": exterior,
        "team_photo_count": team,
        "video_count": problems.videos,
        "has_profile_photo": problems.logo,
        "has_cover_photo": problems.cover,
        "last_photo_uploaded_on": (
            data.reference - timedelta(days=problems.photo_age_days) if problems.photos else None
        ),
    }


def _posts(data: ProfileData, rng: random.Random) -> None:
    archetype, problems = data.archetype, data.archetype.problems
    if not problems.post_types:
        return  # never posted at all: the gap check owns that, at critical severity

    ages = [problems.last_post_days]
    ages += spread(rng, max(0, problems.posts_90d - 1), problems.last_post_days + 4, 89)
    # Enough posts inside the 180-day window for the mix and call-to-action checks to run.
    older_start = max(problems.last_post_days + 6, 92)
    ages += spread(rng, max(0, 5 - len(ages)), older_start, 178)
    ages = sorted({age for age in ages if age >= problems.last_post_days})

    with_cta = round(problems.post_cta_share * len(ages))
    for index, days_ago in enumerate(ages):
        data.posts.append(
            {
                "google_post_id": f"demo-{archetype.key}-post-{index:03d}",
                "post_type": problems.post_types[index % len(problems.post_types)],
                "summary": archetype.posts[index % len(archetype.posts)],
                "cta_type": POST_CTAS[index % len(POST_CTAS)] if index < with_cta else None,
                "published_on": data.reference - timedelta(days=days_ago),
            }
        )


# ---- operations ----------------------------------------------------------------------


def _bookings(data: ProfileData, rng: random.Random) -> None:
    archetype, problems = data.archetype, data.archetype.problems
    mix = problems.bookings
    reference = data.reference
    plan: list[tuple[str, bool]] = (
        [("new", True)] * mix.expired
        + [("new", False)] * max(0, mix.new_stale - mix.expired)
        + [("confirmed", False)] * mix.confirmed
        + [("completed", True)] * mix.completed
        + [("cancelled", True)] * mix.cancelled
        + [("no_show", True)] * mix.no_show
    )
    rng.shuffle(plan)

    services = list(archetype.booking_services)
    unlisted = list(problems.unlisted_services)
    ages = spread(rng, len(plan), 4, 88)
    rng.shuffle(ages)
    weekend_left = problems.weekend_requests

    for index, ((status, past), created_days) in enumerate(zip(plan, ages, strict=True)):
        # Confirmed visits are upcoming, so they were requested recently.
        if status == "confirmed":
            created_days = min(created_days, 24)
        lead = _lead(problems, created_days, past, rng)
        requested = reference - timedelta(days=created_days) + timedelta(days=lead)
        if weekend_left:
            # Alternate Saturday and Sunday so both weekend days carry real demand.
            target = 5 if weekend_left % 2 else 6
            moved = requested + timedelta(days=(target - requested.weekday()) % 7)
            if (moved < reference) if past else (moved >= reference):
                requested = moved
                weekend_left -= 1
        service = (
            unlisted[index % len(unlisted)]
            if unlisted and index % 9 == 0
            else services[index % len(services)]
        )
        channel = (
            BOOKING_CHANNELS[0]
            if rng.random() < problems.dominant_channel_share
            else rng.choice(BOOKING_CHANNELS[1:])
        )
        data.bookings.append(
            {
                "external_booking_id": f"DEMO-{archetype.key.upper()}-{index:03d}",
                "customer_name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_INITIALS)}.",
                "service": service,
                "requested_for_date": requested,
                "status": status,
                "booking_source": channel,
                "booking_created_at": at(reference, created_days, hour=10 + index % 8),
            }
        )


def _lead(problems, created_days: int, past: bool, rng: random.Random) -> int:
    """Days between the request and the date asked for, respecting the status.

    A settled or expired request must ask for a date that has already passed; a new or
    confirmed one must ask for a date still to come. `lead_collapse` then pulls the
    recent slice's median down far enough for the trend check to see it.
    """
    recent = created_days <= 27
    if problems.lead_collapse:
        pool = (1, 2, 3, 4) if recent else (24, 28, 32, 36, 40)
    else:
        pool = (7, 10, 14, 18, 21)
    lead = rng.choice(pool)
    if past:
        return max(1, min(lead, created_days - 2)) if created_days > 3 else 1
    return lead if lead > created_days else created_days + 4
