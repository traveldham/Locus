"""Visibility worker: does the profile show up when people search, and against whom?

Five groups of checks, all deterministic:

- Tracking: are the weekly rank checks fresh enough to judge anything?
- Presence: how many tracked keywords make the three-result local pack, which ones
  slipped out of it, and which sit just below it where one push would count?
- Reach: keywords never found, keywords that fell, high-intent keywords lagging the
  rest, and the branded term.
- Demand: search terms that surfaced the profile last month and are losing volume, and
  services the operator sells that no search term mentions.
- Rivals: businesses ranked ahead on several keywords with more reviews, a higher
  rating or more photos than this location.

Ranks are weekly and a keyword not found has no position, never rank zero. Competitors
are only compared inside the same keyword and week. Google withholds exact impressions
for low-volume terms (`is_threshold`); those rows are never compared. Suggestions for
the fields marked `suggests` are drafted afterwards by the suggestion layer, never here.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta
from statistics import mean, median
from typing import TYPE_CHECKING

from app.services.recommendations.grading import graded
from app.services.recommendations.values import day, number

if TYPE_CHECKING:
    from app.services.recommendations.context import Context

KEY = "visibility"
LABEL = "Local visibility"
WEIGHT = 25

PACK_SIZE = 3
# Words that describe the trade rather than the brand; never treated as a brand word.
GENERIC_WORDS = {
    "dental",
    "dentist",
    "dentistry",
    "clinic",
    "care",
    "family",
    "group",
    "center",
    "centre",
    "the",
    "and",
    "of",
    "smile",
    "smiles",
}


def check(
    weight: int,
    label: str,
    checks: str,
    fix: str,
    *,
    unit: str = "location",
    predicate: str,
    predicate_one: str,
    subject: str | None = None,
    subject_predicate: str | None = None,
    suggests: str | None = None,
    group: str = "presence",
    effort: str = "hour",
) -> dict:
    return {
        "weight": weight,
        "group": group,
        "effort": effort,
        "label": label,
        "checks": checks,
        "fix": fix,
        "unit": unit,
        "predicate": predicate,
        "predicate_one": predicate_one,
        "subject": subject,
        "subject_predicate": subject_predicate,
        "suggests": suggests,
    }


CHECKS: dict[str, dict] = {
    # Tracking
    "tracking_stale": check(
        2,
        "Rank tracking is stale",
        "Whether the latest weekly rank check falls inside the freshness window.",
        "Restart the rank tracker for this location. Without a recent check no ranking "
        "finding can be trusted, so the rank checks are skipped until it runs again.",
        predicate="have stale rank tracking",
        predicate_one="has stale rank tracking",
    ),
    # Presence
    "pack_share_low": check(
        3,
        "Few keywords in the local pack",
        "The share of tracked keywords ranked in the three-result local pack in the latest "
        "week, against the configured minimum.",
        "Work the near-pack keywords first: tighten the primary category, add the matching "
        "service and attribute, and keep reviews arriving. The pack is where calls and "
        "direction requests come from.",
        predicate="have few keywords in the local pack",
        predicate_one="has few keywords in the local pack",
    ),
    "pack_lost": check(
        2,
        "Keyword dropped out of the local pack",
        "Keywords that were in the local pack earlier in the trend window but not in the "
        "latest week.",
        "Check what changed: a category edit, a run of poor reviews, a new rival, or a "
        "closure flag. Regaining a pack spot is far cheaper than earning a new one.",
        unit="keyword",
        predicate="dropped out of the local pack",
        predicate_one="dropped out of the local pack",
        subject="keyword",
        subject_predicate="dropped out of the local pack",
    ),
    "near_pack_opportunity": check(
        2,
        "Keyword just below the local pack",
        "Keywords ranked in the near-pack band (positions 4 to 8) in at least the configured "
        "number of recent weeks. An opportunity, not a fault.",
        "Give each of these keywords one concrete push: a matching service or category, a "
        "post about it, or an attribute that proves it. One or two positions is all it takes.",
        unit="keyword",
        predicate="sit just below the local pack",
        predicate_one="sits just below the local pack",
        subject="keyword",
        subject_predicate="sit just below the local pack",
        suggests="keyword_plan",
    ),
    # Reach
    "not_found_persistent": check(
        3,
        "Keyword never found",
        "Keywords where the profile did not appear at all for the configured number of "
        "consecutive weeks ending in the latest.",
        "Confirm the profile is relevant to the term at all: the right category, the "
        "service listed, the area served. If it is, the term may simply be outside reach.",
        unit="keyword",
        predicate="were not found for weeks",
        predicate_one="was not found for weeks",
        subject="keyword",
        subject_predicate="were not found for weeks",
    ),
    "rank_dropped": check(
        2,
        "Keyword fell in rank",
        "Keywords whose latest position is worse than their average over the previous weeks "
        "by the configured number of positions.",
        "Look for a cause dated to the drop: a profile edit, a review, a rival's new "
        "listing. One week can be noise; act when the next check confirms it.",
        unit="keyword",
        predicate="fell in rank",
        predicate_one="fell in rank",
        subject="keyword",
        subject_predicate="fell in rank",
    ),
    "high_intent_lagging": check(
        2,
        "High-intent keyword lags the rest",
        "Keywords with a high-intent search intent whose latest position is behind the "
        "location's other keywords by the configured margin, or not found at all.",
        "These are the searches that turn into appointments. Add the service and the "
        "matching category and attribute, and describe it on the profile.",
        unit="keyword",
        predicate="lag on high-intent searches",
        predicate_one="lags on a high-intent search",
        subject="keyword",
        subject_predicate="lag the location's other keywords",
        suggests="keyword_plan",
    ),
    "branded_not_first": check(
        3,
        "Branded search not in first place",
        "Whether a tracked keyword carrying the business name ranks first.",
        "A brand search that does not return the profile first usually means a duplicate "
        "listing, a name mismatch or an unverified profile. Fix that before anything else.",
        unit="keyword",
        predicate="do not rank first on their own name",
        predicate_one="does not rank first on its own name",
        subject="keyword",
        subject_predicate="do not rank first",
    ),
    # Demand
    "search_term_losing": check(
        2,
        "Search term losing impressions",
        "Search terms that surfaced the profile in the last two complete months and lost the "
        "configured share of impressions month over month, above a minimum volume.",
        "Check that the profile still speaks to the term: the service, the category, the "
        "hours it implies. A falling term is demand the profile is no longer matched to.",
        unit="search term",
        predicate="lost impressions month over month",
        predicate_one="lost impressions month over month",
        subject="search term",
        subject_predicate="lost impressions",
        suggests="term_action",
    ),
    "service_not_surfacing": check(
        1,
        "Service never appears in search terms",
        "Services from the project list that no search term in the latest complete month mentions.",
        "Add the service to the profile's services list, use its name in a post, and confirm "
        "the matching category is set so searches for it can reach the profile.",
        unit="service",
        predicate="never appear in search terms",
        predicate_one="never appears in search terms",
        subject="service",
        subject_predicate="never appear in search terms",
    ),
    # Rivals
    "rival_ahead_gap": check(
        2,
        "Rival ahead with a stronger profile",
        "Businesses ranked ahead of this location on several keywords in the latest week "
        "whose review count, rating or photo count clearly beats this profile's.",
        "Close the named gap: a steady flow of reviews, replies that lift the rating, or a "
        "batch of real photos. Rivals ahead on several terms set the bar Google compares to.",
        unit="rival",
        predicate="are ahead with a stronger profile",
        predicate_one="is ahead with a stronger profile",
        subject="rival",
        subject_predicate="are ahead on several keywords",
    ),
}

GROUPS = {
    "tracking": ("tracking_stale",),
    "presence": ("pack_share_low", "pack_lost", "near_pack_opportunity"),
    "reach": ("not_found_persistent", "rank_dropped", "high_intent_lagging", "branded_not_first"),
    "demand": ("search_term_losing", "service_not_surfacing"),
    "rivals": ("rival_ahead_gap",),
}
GROUP_LABELS = {
    "tracking": "Tracking",
    "presence": "Local pack",
    "reach": "Keywords",
    "demand": "Search demand",
    "rivals": "Rivals",
}
EFFORT = {
    "minutes": ("tracking_stale", "service_not_surfacing"),
    "hour": ("near_pack_opportunity", "rank_dropped", "search_term_losing", "branded_not_first"),
    "afternoon": (
        "pack_share_low",
        "pack_lost",
        "not_found_persistent",
        "high_intent_lagging",
        "rival_ahead_gap",
    ),
}
for _group, _rules in GROUPS.items():
    for _rule in _rules:
        CHECKS[_rule]["group"] = _group
for _effort, _rules in EFFORT.items():
    for _rule in _rules:
        CHECKS[_rule]["effort"] = _effort
assert {r for rules in GROUPS.values() for r in rules} == set(CHECKS)
assert {r for rules in EFFORT.values() for r in rules} == set(CHECKS)

RANK_RULES = (
    "pack_share_low",
    "pack_lost",
    "near_pack_opportunity",
    "not_found_persistent",
    "rank_dropped",
    "high_intent_lagging",
    "branded_not_first",
    "rival_ahead_gap",
)


def words(text) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text or "").casefold())


def brand_words(loc: dict) -> set[str]:
    """Distinctive words of the stored name: not the trade, not the place."""
    place = set(words(loc.get("locality"))) | set(words(loc.get("administrative_area")))
    trade = set(words(loc.get("primary_category_display"))) | GENERIC_WORDS
    return {w for w in words(loc.get("title")) if len(w) >= 4 and w not in place | trade}


def is_branded(keyword: str, loc: dict) -> bool:
    brand = brand_words(loc)
    return bool(brand) and bool(brand & set(words(keyword)))


def position(row: dict | None) -> int | None:
    """The absolute rank, or None when the profile was not found that week."""
    if not row or not row.get("found"):
        return None
    value = row.get("rank_absolute")
    return int(value) if number(value) and value >= 1 else None


def in_pack(row: dict | None) -> bool:
    return (
        bool(row)
        and number(row.get("rank_in_local_pack"))
        and 1 <= row["rank_in_local_pack"] <= PACK_SIZE
    )


def rank_table(c: Context) -> dict[str, dict[str, dict]]:
    """keyword id -> week (ISO) -> rank row."""
    table: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in c.rows("ranks"):
        week = day(row.get("week_start"))
        if week:
            table[str(row.get("tracked_keyword_id"))][week.isoformat()] = row
    return table


def trend_weeks(latest: date, count: int) -> list[str]:
    """The `count` weekly slots ending at `latest`, oldest first."""
    return [(latest - timedelta(weeks=count - 1 - i)).isoformat() for i in range(count)]


def previous_month(as_of: date) -> str:
    first = as_of.replace(day=1)
    return (first - timedelta(days=1)).strftime("%Y-%m")


def month_before(year_month: str) -> str:
    year, month = int(year_month[:4]), int(year_month[5:7])
    return f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"


def project_services(c: Context) -> list[str]:
    seen: dict[str, None] = {}
    for project in c.snapshot.get("projects", []):
        for service in project.get("services") or []:
            if isinstance(service, str) and service.strip():
                seen.setdefault(service.strip(), None)
    return list(seen)


def own_profile_stats(c: Context) -> dict:
    reviews = c.rows("reviews")
    ratings = [r["star_rating"] for r in reviews if number(r.get("star_rating"))]
    media = c.rows("media")
    photos = media[0].get("photo_count") if media else None
    return {
        "review_count": len(reviews) if reviews else None,
        "average_rating": round(mean(ratings), 2) if ratings else None,
        "photo_count": int(photos) if number(photos) else None,
    }


def evaluate(c: Context) -> None:
    loc = c.location
    href = "/insights/search"
    if loc.get("open_status") == "closed_permanently":
        for rule in CHECKS:
            c.assess(rule, "suppressed", "Permanently closed: the profile is not audited.")
        return

    keywords = {str(k["id"]): k for k in c.rows("keywords")}
    table = rank_table(c)
    weeks = sorted({w for rows in table.values() for w in rows})
    latest = day(weeks[-1]) if weeks else None

    if not keywords or latest is None:
        c.assess("tracking_stale", "insufficient_data", "No tracked keywords or rank checks.")
        for rule in RANK_RULES:
            c.assess(rule, "insufficient_data", "No rank checks stored for this location.")
    elif (c.as_of - latest).days > c.config.rank_freshness_days:
        c.assess(
            "tracking_stale",
            "triggered",
            f"Latest rank check is from the week of {latest}, "
            f"{(c.as_of - latest).days} days before {c.as_of}.",
            1,
        )
        c.emit(
            "tracking_stale",
            "Restart rank tracking",
            CHECKS["tracking_stale"]["fix"],
            f"The latest weekly rank check is from the week of {latest}, "
            f"{(c.as_of - latest).days} days before the analysis date; the freshness window "
            f"is {c.config.rank_freshness_days} days.",
            graded(50, ((c.as_of - latest).days - c.config.rank_freshness_days) / 28, 15, 70),
            [
                c.evidence(
                    "ranks",
                    [r for rows in table.values() for r in rows.values()],
                    ["week_start"],
                    "as_of minus max(week_start)",
                    latest_week=latest.isoformat(),
                    age_days=(c.as_of - latest).days,
                )
            ],
            href,
            "Rank checks are our own tracker's observations, not Google data.",
            "high",
        )
        for rule in RANK_RULES:
            c.assess(rule, "insufficient_data", "Rank tracking is stale; ranks not judged.")
    else:
        c.assess("tracking_stale", "clear", f"Latest rank check is the week of {latest}.")
        _ranks(c, loc, href, keywords, table, latest)

    _demand(c, loc, href)


def _ranks(
    c: Context,
    loc: dict,
    href: str,
    keywords: dict[str, dict],
    table: dict[str, dict[str, dict]],
    latest: date,
) -> None:
    cfg = c.config
    weeks = trend_weeks(latest, cfg.rank_trend_weeks)
    latest_key = latest.isoformat()
    tracked = {kid: k for kid, k in keywords.items() if kid in table}
    name = lambda kid: str(keywords[kid].get("keyword") or kid)  # noqa: E731 - tiny helper

    # Pack share in the latest week.
    latest_rows = {kid: table[kid].get(latest_key) for kid in tracked}
    judged = {kid: r for kid, r in latest_rows.items() if r is not None}
    packed = [kid for kid, r in judged.items() if in_pack(r)]
    if not judged:
        c.assess(
            "pack_share_low", "insufficient_data", "No keyword was checked in the latest week."
        )
    else:
        share = len(packed) / len(judged)
        if share < cfg.pack_share_min:
            c.assess(
                "pack_share_low",
                "triggered",
                f"{len(packed)} of {len(judged)} keywords in the local pack ({share:.0%}).",
                len(judged) - len(packed),
                len(judged),
            )
            c.emit(
                "pack_share_low",
                "Win more local pack spots",
                CHECKS["pack_share_low"]["fix"],
                f"In the week of {latest}, {len(packed)} of {len(judged)} tracked keywords "
                f"put the profile in the three-result local pack ({share:.0%}); the policy "
                f"minimum is {cfg.pack_share_min:.0%}.",
                graded(45, (cfg.pack_share_min - share) / cfg.pack_share_min, 20, 65),
                [
                    c.evidence(
                        "ranks",
                        list(judged.values()),
                        ["rank_in_local_pack", "week_start"],
                        "count(rank_in_local_pack in 1..3) / count(keywords checked), latest week",
                        in_pack=[name(k) for k in packed],
                        share=round(share, 3),
                        minimum=cfg.pack_share_min,
                    )
                ],
                href,
                "Ranks come from our tracker at one checkpoint per week, not from Google.",
                "high",
            )
        else:
            c.assess(
                "pack_share_low", "clear", f"{len(packed)} of {len(judged)} keywords in the pack."
            )

    # Lost the pack: in it during an earlier trend week, not in the latest.
    lost = [
        kid
        for kid, r in judged.items()
        if not in_pack(r) and any(in_pack(table[kid].get(w)) for w in weeks[:-1])
    ]
    if not judged:
        c.assess("pack_lost", "insufficient_data", "No keyword was checked in the latest week.")
    elif lost:
        c.assess(
            "pack_lost",
            "triggered",
            f"{len(lost)} of {len(judged)} keywords left the local pack.",
            len(lost),
            len(judged),
        )
        for kid in lost:
            last_in = max(w for w in weeks[:-1] if in_pack(table[kid].get(w)))
            now = position(judged[kid])
            c.emit(
                "pack_lost",
                f"“{name(kid)}” dropped out of the local pack",
                CHECKS["pack_lost"]["fix"],
                f"“{name(kid)}” was in the local pack in the week of {last_in} and is "
                + (f"now at position {now}." if now else "now not found at all."),
                graded(48, 0.5 if now is None else 0.0, 12, 60),
                [
                    c.evidence(
                        "ranks",
                        [table[kid][w] for w in weeks if w in table[kid]],
                        ["week_start", "rank_in_local_pack", "rank_absolute"],
                        "in pack in an earlier trend week, not in the latest",
                        keyword=name(kid),
                        last_in_pack=last_in,
                        latest_position=now,
                    )
                ],
                href,
                "One checkpoint per week; a brief dip and a real loss look alike until the "
                "next check.",
                "high",
                subject=name(kid),
            )
    else:
        c.assess("pack_lost", "clear", "No keyword left the local pack this window.")

    # Near-pack opportunities.
    near = {}
    for kid in tracked:
        hits = [
            w
            for w in weeks
            if (p := position(table[kid].get(w))) is not None
            and cfg.near_pack_low <= p <= cfg.near_pack_high
        ]
        if len(hits) >= cfg.near_pack_min_weeks and not in_pack(latest_rows.get(kid)):
            near[kid] = hits
    if not tracked:
        c.assess("near_pack_opportunity", "insufficient_data", "No keywords tracked.")
    elif near:
        c.assess(
            "near_pack_opportunity",
            "triggered",
            f"{len(near)} of {len(tracked)} keywords sit just below the pack.",
            len(near),
            len(tracked),
        )
        for kid, hits in near.items():
            now = position(latest_rows.get(kid))
            c.emit(
                "near_pack_opportunity",
                f"“{name(kid)}” is within reach of the local pack",
                CHECKS["near_pack_opportunity"]["fix"],
                f"“{name(kid)}” ranked between {cfg.near_pack_low} and {cfg.near_pack_high} "
                f"in {len(hits)} of the last {len(weeks)} weeks"
                + (f", most recently at position {now}." if now else "."),
                graded(18, (len(hits) - cfg.near_pack_min_weeks) / max(1, len(weeks) - 1), 10, 32),
                [
                    c.evidence(
                        "ranks",
                        [table[kid][w] for w in weeks if w in table[kid]],
                        ["week_start", "rank_absolute"],
                        f"weeks with rank_absolute in {cfg.near_pack_low}..{cfg.near_pack_high}",
                        keyword=name(kid),
                        weeks_near=hits,
                        latest_position=now,
                        intent=keywords[kid].get("search_intent"),
                    )
                ],
                href,
                "An opportunity ranked by proximity to the pack, not a guarantee of entry.",
                "high",
                subject=name(kid),
            )
    else:
        c.assess("near_pack_opportunity", "clear", "No keyword is parked just below the pack.")

    # Never found for N consecutive weeks ending in the latest.
    span = trend_weeks(latest, cfg.not_found_min_weeks)
    complete = [kid for kid in tracked if all(w in table[kid] for w in span)]
    unfound = [kid for kid in complete if all(not table[kid][w].get("found") for w in span)]
    if not complete:
        c.assess(
            "not_found_persistent",
            "insufficient_data",
            f"No keyword has {cfg.not_found_min_weeks} consecutive weekly checks.",
        )
    elif unfound:
        c.assess(
            "not_found_persistent",
            "triggered",
            f"{len(unfound)} of {len(complete)} keywords not found for "
            f"{cfg.not_found_min_weeks} weeks.",
            len(unfound),
            len(complete),
        )
        for kid in unfound:
            c.emit(
                "not_found_persistent",
                f"“{name(kid)}” never shows the profile",
                CHECKS["not_found_persistent"]["fix"],
                f"The profile was not found for “{name(kid)}” in any of the last "
                f"{cfg.not_found_min_weeks} weekly checks.",
                55,
                [
                    c.evidence(
                        "ranks",
                        [table[kid][w] for w in span],
                        ["week_start", "found"],
                        f"found is false in {cfg.not_found_min_weeks} consecutive weeks",
                        keyword=name(kid),
                        weeks=span,
                    )
                ],
                href,
                "Not found means outside the checked results, not a measured position.",
                "high",
                subject=name(kid),
            )
    else:
        c.assess("not_found_persistent", "clear", "Every keyword was found at least once.")

    # Dropped: latest versus the mean of the earlier trend weeks.
    comparable = {}
    for kid in tracked:
        now = position(latest_rows.get(kid))
        earlier = [p for w in weeks[:-1] if (p := position(table[kid].get(w))) is not None]
        if now is not None and earlier:
            comparable[kid] = (now, mean(earlier))
    dropped = {
        kid: (now, base)
        for kid, (now, base) in comparable.items()
        if now - base >= cfg.rank_drop_min_positions
    }
    if not comparable:
        c.assess("rank_dropped", "insufficient_data", "No keyword has two weeks of positions.")
    elif dropped:
        c.assess(
            "rank_dropped",
            "triggered",
            f"{len(dropped)} of {len(comparable)} keywords fell "
            f"{cfg.rank_drop_min_positions}+ positions.",
            len(dropped),
            len(comparable),
        )
        for kid, (now, base) in dropped.items():
            c.emit(
                "rank_dropped",
                f"“{name(kid)}” fell to position {now}",
                CHECKS["rank_dropped"]["fix"],
                f"“{name(kid)}” averaged position {base:.0f} over the previous weeks and is "
                f"at {now} in the week of {latest}, {now - base:.0f} positions worse.",
                graded(40, (now - base - cfg.rank_drop_min_positions) / 5, 15, 58),
                [
                    c.evidence(
                        "ranks",
                        [table[kid][w] for w in weeks if w in table[kid]],
                        ["week_start", "rank_absolute"],
                        "latest rank_absolute minus mean of earlier weeks in the window",
                        keyword=name(kid),
                        latest_position=now,
                        earlier_mean=round(base, 1),
                    )
                ],
                href,
                "Weekly positions move by a few places on their own; one check is not a trend.",
                subject=name(kid),
            )
    else:
        c.assess("rank_dropped", "clear", "No keyword fell past the threshold.")

    # High-intent keywords lagging the rest.
    intents = {i.casefold() for i in cfg.high_intent_intents}
    high = [
        kid
        for kid in tracked
        if str(keywords[kid].get("search_intent") or "").casefold() in intents
    ]
    others = [
        p
        for kid in tracked
        if kid not in high and (p := position(latest_rows.get(kid))) is not None
    ]
    if not high or not others:
        c.assess(
            "high_intent_lagging",
            "insufficient_data",
            "Needs at least one high-intent keyword and one other keyword with a position.",
        )
    else:
        baseline = median(others)
        lagging = {}
        for kid in high:
            if latest_rows.get(kid) is None:
                continue
            now = position(latest_rows[kid])
            if now is None or now - baseline >= cfg.high_intent_lag_positions:
                lagging[kid] = now
        checked = [kid for kid in high if latest_rows.get(kid) is not None]
        if lagging:
            c.assess(
                "high_intent_lagging",
                "triggered",
                f"{len(lagging)} of {len(checked)} high-intent keywords lag the rest.",
                len(lagging),
                len(checked),
            )
            for kid, now in lagging.items():
                c.emit(
                    "high_intent_lagging",
                    f"“{name(kid)}” lags the location's other keywords",
                    CHECKS["high_intent_lagging"]["fix"],
                    f"“{name(kid)}” ({keywords[kid].get('search_intent')}) is "
                    + (f"at position {now}" if now else "not found")
                    + f" while the location's other keywords sit around position {baseline:.0f}.",
                    graded(46, 1.0 if now is None else (now - baseline) / 10, 12, 60),
                    [
                        c.evidence(
                            "ranks",
                            [latest_rows[kid]],
                            ["rank_absolute", "found"],
                            "latest position versus median of non-high-intent keywords",
                            keyword=name(kid),
                            intent=keywords[kid].get("search_intent"),
                            latest_position=now,
                            baseline_median=baseline,
                        )
                    ],
                    href,
                    "Which intents count as high-intent is a policy list, not a Google label.",
                    "high",
                    subject=name(kid),
                )
        else:
            c.assess(
                "high_intent_lagging", "clear", "High-intent keywords keep pace with the rest."
            )

    # Branded keyword.
    branded = [kid for kid in tracked if is_branded(name(kid), loc)]
    branded_checked = [kid for kid in branded if latest_rows.get(kid) is not None]
    if not branded_checked:
        c.assess("branded_not_first", "insufficient_data", "No branded keyword is tracked.")
    else:
        off = {kid: position(latest_rows[kid]) for kid in branded_checked}
        off = {kid: p for kid, p in off.items() if p != 1}
        if off:
            c.assess(
                "branded_not_first",
                "triggered",
                f"{len(off)} of {len(branded_checked)} branded keywords not first.",
                len(off),
                len(branded_checked),
            )
            for kid, now in off.items():
                c.emit(
                    "branded_not_first",
                    f"“{name(kid)}” does not return the profile first",
                    CHECKS["branded_not_first"]["fix"],
                    f"A search for “{name(kid)}” "
                    + (
                        f"ranks the profile at position {now}."
                        if now
                        else "does not find the profile at all."
                    ),
                    80 if now is None else 60,
                    [
                        c.evidence(
                            "ranks",
                            [latest_rows[kid]],
                            ["rank_absolute", "found"],
                            "latest position for a keyword carrying a brand word",
                            keyword=name(kid),
                            latest_position=now,
                        )
                    ],
                    href,
                    "Branded means the keyword shares a distinctive word with the stored name.",
                    "high",
                    subject=name(kid),
                )
        else:
            c.assess("branded_not_first", "clear", "Branded keywords rank first.")

    _rivals(c, href, keywords, tracked, latest_rows, latest_key)


def _rivals(
    c: Context,
    href: str,
    keywords: dict[str, dict],
    tracked: dict[str, dict],
    latest_rows: dict[str, dict | None],
    latest_key: str,
) -> None:
    cfg = c.config
    ours = own_profile_stats(c)
    name = lambda kid: str(keywords[kid].get("keyword") or kid)  # noqa: E731 - tiny helper
    # Competitor rows are only compared inside the same keyword and week.
    observations = [
        r
        for r in c.snapshot.get("competitors", [])
        if str(r.get("tracked_keyword_id")) in tracked
        and (day(r.get("week_start")) or date.min).isoformat() == latest_key
    ]
    if not observations or all(v is None for v in ours.values()):
        c.assess(
            "rival_ahead_gap",
            "insufficient_data",
            "No competitor observations for the latest week, or nothing of our own to compare.",
        )
        return
    ahead: dict[str, dict] = {}
    for r in observations:
        kid = str(r.get("tracked_keyword_id"))
        mine = latest_rows.get(kid)
        if mine is None:
            continue
        theirs = r.get("rank_absolute")
        if not number(theirs):
            continue
        my_pos = position(mine)
        if my_pos is not None and theirs >= my_pos:
            continue
        key = str(r.get("competitor_place_id") or r.get("competitor_name"))
        entry = ahead.setdefault(
            key, {"name": r.get("competitor_name"), "keywords": [], "rows": [], "gaps": {}}
        )
        entry["keywords"].append((name(kid), int(theirs), my_pos))
        entry["rows"].append(r)
        if (
            ours["review_count"] is not None
            and number(r.get("review_count"))
            and r["review_count"] >= ours["review_count"] * cfg.rival_review_ratio
        ):
            entry["gaps"]["reviews"] = max(entry["gaps"].get("reviews", 0), int(r["review_count"]))
        if (
            ours["average_rating"] is not None
            and number(r.get("average_rating"))
            and r["average_rating"] >= ours["average_rating"] + cfg.rival_rating_gap
        ):
            entry["gaps"]["rating"] = max(
                entry["gaps"].get("rating", 0), float(r["average_rating"])
            )
        if (
            ours["photo_count"] is not None
            and number(r.get("photo_count"))
            and r["photo_count"] >= max(1, ours["photo_count"]) * cfg.rival_photo_ratio
        ):
            entry["gaps"]["photos"] = max(entry["gaps"].get("photos", 0), int(r["photo_count"]))
    rivals = {k: v for k, v in ahead.items() if len(v["keywords"]) >= cfg.rival_min_keywords_ahead}
    gapped = {k: v for k, v in rivals.items() if v["gaps"]}
    if not rivals:
        c.assess("rival_ahead_gap", "clear", "No rival is ahead on several keywords.")
        return
    if not gapped:
        c.assess(
            "rival_ahead_gap",
            "clear",
            f"{len(rivals)} rivals ahead on several keywords, none with a clearly stronger "
            "profile.",
        )
        return
    c.assess(
        "rival_ahead_gap",
        "triggered",
        f"{len(gapped)} of {len(rivals)} rivals ahead on several keywords have a stronger profile.",
        len(gapped),
        len(rivals),
    )
    labels = {"reviews": "more reviews", "rating": "a higher rating", "photos": "more photos"}
    for entry in sorted(gapped.values(), key=lambda e: -len(e["keywords"])):
        parts = []
        if "reviews" in entry["gaps"]:
            parts.append(f"{entry['gaps']['reviews']} reviews to our {ours['review_count']}")
        if "rating" in entry["gaps"]:
            parts.append(
                f"a {entry['gaps']['rating']:.1f} rating to our {ours['average_rating']:.1f}"
            )
        if "photos" in entry["gaps"]:
            parts.append(f"{entry['gaps']['photos']} photos to our {ours['photo_count']}")
        terms = ", ".join(f"“{k}”" for k, _, _ in entry["keywords"][:4])
        c.emit(
            "rival_ahead_gap",
            f"{entry['name']} is ahead on {len(entry['keywords'])} keywords with "
            + " and ".join(labels[g] for g in entry["gaps"]),
            CHECKS["rival_ahead_gap"]["fix"],
            f"{entry['name']} ranks ahead of the profile on {terms}"
            + (" and more" if len(entry["keywords"]) > 4 else "")
            + " and has "
            + "; ".join(parts)
            + ".",
            graded(30, (len(entry["keywords"]) - cfg.rival_min_keywords_ahead) / 6, 18, 50),
            [
                c.evidence(
                    "competitors",
                    entry["rows"],
                    [
                        "competitor_name",
                        "rank_absolute",
                        "review_count",
                        "average_rating",
                        "photo_count",
                    ],
                    "rival rank_absolute below ours in the same keyword and week; profile "
                    "figures compared to our reviews and media rows",
                    rival=entry["name"],
                    keywords=[
                        {"keyword": k, "rival_position": t, "our_position": m}
                        for k, t, m in entry["keywords"]
                    ],
                    gaps=entry["gaps"],
                    ours=ours,
                )
            ],
            href,
            "A rival's figures are what our tracker observed that week, not Google's own data.",
            subject=str(entry["name"]),
        )


def _demand(c: Context, loc: dict, href: str) -> None:
    cfg = c.config
    terms = c.rows("search_terms")
    months = sorted({str(r.get("year_month")) for r in terms if r.get("year_month")})
    latest = months[-1] if months else None
    # The month of as_of is incomplete; the latest complete month is the one before it,
    # and the data must reach it to be current.
    if latest is None or latest < previous_month(c.as_of - timedelta(days=31)):
        c.assess(
            "search_term_losing", "insufficient_data", "No recent monthly search terms stored."
        )
        c.assess(
            "service_not_surfacing", "insufficient_data", "No recent monthly search terms stored."
        )
        return
    prior = month_before(latest)
    by_term: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in terms:
        by_term[str(r.get("search_term") or "").strip().casefold()][str(r.get("year_month"))] = r
    paired = {}
    for term, rows in by_term.items():
        a, b = rows.get(prior), rows.get(latest)
        if (
            a
            and b
            and not a.get("is_threshold")
            and not b.get("is_threshold")
            and number(a.get("impressions"))
            and number(b.get("impressions"))
            and a["impressions"] >= cfg.term_loss_min_impressions
        ):
            paired[term] = (a, b)
    if not paired:
        c.assess(
            "search_term_losing",
            "insufficient_data",
            f"No search term has exact impressions in both {prior} and {latest} above the minimum.",
        )
    else:
        losing = {
            t: (a, b)
            for t, (a, b) in paired.items()
            if (a["impressions"] - b["impressions"]) / a["impressions"] >= cfg.term_loss_share
        }
        if losing:
            c.assess(
                "search_term_losing",
                "triggered",
                f"{len(losing)} of {len(paired)} paired terms lost "
                f"{cfg.term_loss_share:.0%}+ of impressions.",
                len(losing),
                len(paired),
            )
            for term, (a, b) in sorted(losing.items(), key=lambda kv: -kv[1][0]["impressions"]):
                drop = (a["impressions"] - b["impressions"]) / a["impressions"]
                label = str(b.get("search_term") or term)
                c.emit(
                    "search_term_losing",
                    f"“{label}” lost {drop:.0%} of its impressions",
                    CHECKS["search_term_losing"]["fix"],
                    f"“{label}” surfaced the profile {a['impressions']} times in {prior} and "
                    f"{b['impressions']} times in {latest}, a {drop:.0%} drop.",
                    graded(35, (drop - cfg.term_loss_share) / (1 - cfg.term_loss_share), 15, 55),
                    [
                        c.evidence(
                            "search_terms",
                            [a, b],
                            ["year_month", "search_term", "impressions", "is_threshold"],
                            "(prior - latest) / prior, exact months only",
                            term=label,
                            prior_month=prior,
                            latest_month=latest,
                            prior_impressions=a["impressions"],
                            latest_impressions=b["impressions"],
                            drop=round(drop, 3),
                        )
                    ],
                    href,
                    "Google truncates the long tail and rounds counts, so small terms move "
                    "for reasons the profile cannot control.",
                    subject=label,
                )
        else:
            c.assess("search_term_losing", "clear", "No paired term lost past the threshold.")

    services = project_services(c)
    latest_terms = [
        str(r.get("search_term") or "").casefold()
        for r in terms
        if str(r.get("year_month")) == latest
    ]
    if not services or not latest_terms:
        c.assess(
            "service_not_surfacing",
            "insufficient_data",
            "Needs a project service list and search terms for the latest month.",
        )
        return
    absent = [
        s for s in services if not any(w in t for w in words(s) if len(w) > 3 for t in latest_terms)
    ]
    if absent:
        c.assess(
            "service_not_surfacing",
            "triggered",
            f"{len(absent)} of {len(services)} services never appear in {latest} search terms.",
            len(absent),
            len(services),
        )
        for service in absent:
            c.emit(
                "service_not_surfacing",
                f"No search term mentions “{service}”",
                CHECKS["service_not_surfacing"]["fix"],
                f"None of the {len(latest_terms)} search terms that surfaced the profile in "
                f"{latest} contains a word from “{service}”.",
                22,
                [
                    c.evidence(
                        "search_terms",
                        [r for r in terms if str(r.get("year_month")) == latest],
                        ["search_term", "year_month"],
                        "no latest-month term contains a service word longer than three letters",
                        service=service,
                        month=latest,
                    )
                ],
                href,
                "Word matching against Google's truncated term list; a service can be searched "
                "for under other words.",
                subject=service,
            )
    else:
        c.assess("service_not_surfacing", "clear", "Every listed service appears in a search term.")


def card(snapshot: dict) -> dict:
    """What the tracker sees: keywords, positions, terms and rivals, for the card."""
    loc = snapshot["locations"][0]
    location_id = loc["id"]
    rows = lambda source: [  # noqa: E731 - tiny local helper
        r for r in snapshot.get(source, []) if r.get("location_id") == location_id
    ]
    keywords = {str(k["id"]): k for k in rows("keywords")}
    table: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in rows("ranks"):
        week = day(r.get("week_start"))
        if week and str(r.get("tracked_keyword_id")) in keywords:
            table[str(r.get("tracked_keyword_id"))][week.isoformat()] = r
    weeks_all = sorted({w for v in table.values() for w in v})
    latest = day(weeks_all[-1]) if weeks_all else None
    weeks = trend_weeks(latest, 4) if latest else []
    entries = []
    for kid, k in keywords.items():
        trend = [position(table[kid].get(w)) for w in weeks]
        latest_row = table[kid].get(weeks[-1]) if weeks else None
        entries.append(
            {
                "keyword": k.get("keyword"),
                "intent": k.get("search_intent"),
                "device": k.get("device"),
                "position": position(latest_row),
                "in_pack": in_pack(latest_row),
                "trend": trend,
                "weeks_in_pack": sum(1 for w in weeks if in_pack(table[kid].get(w))),
            }
        )
    entries.sort(key=lambda e: (e["position"] is None, e["position"] or 0, e["keyword"] or ""))
    near = [
        e
        for e in entries
        if sum(1 for p in e["trend"] if p is not None and 4 <= p <= 8) >= 2 and not e["in_pack"]
    ]
    found = [e for e in entries if e["position"] is not None]

    terms = rows("search_terms")
    months = sorted({str(r.get("year_month")) for r in terms if r.get("year_month")})
    top_terms = []
    if months:
        prior = month_before(months[-1])
        by_term = {str(r.get("search_term")): r for r in terms if str(r.get("year_month")) == prior}
        current = [r for r in terms if str(r.get("year_month")) == months[-1]]
        current.sort(key=lambda r: -(r.get("impressions") or 0))
        for r in current[:5]:
            before = by_term.get(str(r.get("search_term")))
            change = None
            if (
                before
                and number(before.get("impressions"))
                and before["impressions"]
                and not before.get("is_threshold")
                and not r.get("is_threshold")
                and number(r.get("impressions"))
            ):
                change = round(
                    (r["impressions"] - before["impressions"]) / before["impressions"], 3
                )
            top_terms.append(
                {
                    "term": r.get("search_term"),
                    "impressions": r.get("impressions"),
                    "is_threshold": bool(r.get("is_threshold")),
                    "change": change,
                }
            )

    rivals: dict[str, dict] = {}
    if latest:
        latest_key = latest.isoformat()
        for r in snapshot.get("competitors", []):
            kid = str(r.get("tracked_keyword_id"))
            if (
                kid not in keywords
                or (day(r.get("week_start")) or date.min).isoformat() != latest_key
            ):
                continue
            mine = position(table[kid].get(latest_key))
            theirs = r.get("rank_absolute")
            if not number(theirs) or (mine is not None and theirs >= mine):
                continue
            key = str(r.get("competitor_place_id") or r.get("competitor_name"))
            entry = rivals.setdefault(
                key,
                {
                    "name": r.get("competitor_name"),
                    "keywords_ahead": 0,
                    "review_count": r.get("review_count"),
                    "average_rating": r.get("average_rating"),
                    "photo_count": r.get("photo_count"),
                },
            )
            entry["keywords_ahead"] += 1
    rivals_ahead = sorted(rivals.values(), key=lambda e: -e["keywords_ahead"])[:5]

    return {
        "latest_week": latest.isoformat() if latest else None,
        "weeks": weeks,
        "keywords_tracked": len(entries),
        "in_pack": sum(1 for e in entries if e["in_pack"]),
        "near_pack": len(near),
        "not_found": sum(1 for e in entries if weeks and e["position"] is None),
        "pack_share": (
            round(sum(1 for e in entries if e["in_pack"]) / len(entries), 3) if entries else None
        ),
        "best": {"keyword": found[0]["keyword"], "position": found[0]["position"]}
        if found
        else None,
        "worst": {"keyword": found[-1]["keyword"], "position": found[-1]["position"]}
        if found
        else None,
        "keywords": entries,
        "top_terms": top_terms,
        "terms_month": months[-1] if months else None,
        "rivals_ahead": rivals_ahead,
        "ours": {
            "review_count": len(rows("reviews")) or None,
            "average_rating": (
                round(
                    mean(
                        [r["star_rating"] for r in rows("reviews") if number(r.get("star_rating"))]
                    ),
                    2,
                )
                if any(number(r.get("star_rating")) for r in rows("reviews"))
                else None
            ),
            "photo_count": (rows("media") or [{}])[0].get("photo_count"),
        },
    }
