"""Visibility worker: every check passes, fails, or abstains for the right reason.

Mutation tests: change one input, one verdict changes. Missing evidence abstains.
"""

from datetime import date

from app.services.recommendations.categories import visibility
from app.services.recommendations.engine import analyze, run_worker
from app.services.recommendations.types import EngineConfig

AS_OF = date(2026, 9, 11)
LOC = "loc-1"
WEEKS = ["2026-08-17", "2026-08-24", "2026-08-31", "2026-09-07"]

KEYWORDS = {
    "k1": ("brightpath dental austin", "general", 1),
    "k2": ("dentist austin", "general", 2),
    "k3": ("emergency dentist austin", "emergency", 3),
    "k4": ("dentist open saturday austin", "general", 10),
}


def rank(kid: str, week: str, pos: int | None) -> dict:
    return {
        "id": f"r-{kid}-{week}",
        "location_id": LOC,
        "tracked_keyword_id": kid,
        "week_start": week,
        "rank_absolute": pos,
        "rank_in_local_pack": pos if pos is not None and pos <= 3 else None,
        "found": pos is not None,
    }


def rival(kid: str, week: str, name: str, pos: int, reviews=50, rating=4.0, photos=20) -> dict:
    return {
        "id": f"c-{kid}-{week}-{name}",
        "tracked_keyword_id": kid,
        "week_start": week,
        "competitor_name": name,
        "competitor_place_id": f"place-{name}",
        "rank_absolute": pos,
        "review_count": reviews,
        "average_rating": rating,
        "photo_count": photos,
    }


def term(month: str, text: str, impressions: int, threshold=False) -> dict:
    return {
        "id": f"t-{month}-{text}",
        "location_id": LOC,
        "year_month": month,
        "search_term": text,
        "impressions": impressions,
        "is_threshold": threshold,
    }


def healthy() -> dict:
    """A profile that passes every visibility check."""
    ranks = [rank(kid, w, pos) for kid, (_, _, pos) in KEYWORDS.items() for w in WEEKS]
    competitors = []
    for kid, (_, _, pos) in KEYWORDS.items():
        for w in WEEKS:
            # Three rivals per keyword-week: ahead of us only on the keyword we rank 10th.
            base = 1 if pos == 10 else pos + 1
            competitors += [rival(kid, w, f"Rival {n}", base + n) for n in range(3)]
    return {
        "locations": [
            {
                "id": LOC,
                "title": "Brightpath Dental",
                "source": "fixture",
                "primary_category_display": "Dentist",
                "locality": "Austin",
                "administrative_area": "TX",
                "open_status": "open",
            }
        ],
        "keywords": [
            {
                "id": kid,
                "location_id": LOC,
                "keyword": text,
                "search_intent": intent,
                "device": "mobile",
            }
            for kid, (text, intent, _) in KEYWORDS.items()
        ],
        "ranks": ranks,
        "competitors": competitors,
        "reviews": [
            {"id": f"rev-{i}", "location_id": LOC, "star_rating": 5 if i % 2 else 4}
            for i in range(100)
        ],
        "media": [{"id": "m1", "location_id": LOC, "photo_count": 40}],
        "search_terms": [
            term("2026-07", "dentist austin", 500),
            term("2026-08", "dentist austin", 520),
            term("2026-07", "teeth whitening austin", 300),
            term("2026-08", "teeth whitening austin", 310),
            term("2026-07", "invisalign near me", 250),
            term("2026-08", "invisalign near me", 260),
        ],
        "projects": [
            {
                "id": "p1",
                "name": "Brightpath Dental Group",
                "website_url": "https://example.org",
                "description": "Family dental group.",
                "services": ["Teeth whitening", "Invisalign"],
                "slug": "bdg",
                "status": "active",
            }
        ],
    }


def verdicts(snapshot, config=None, as_of=AS_OF):
    result = run_worker(snapshot, as_of, config or EngineConfig(), "visibility")
    return {e["rule"]: e for e in result["evaluations"]}, result["items"]


def set_ranks(snapshot, kid, positions):
    snapshot["ranks"] = [r for r in snapshot["ranks"] if r["tracked_keyword_id"] != kid] + [
        rank(kid, w, p) for w, p in zip(WEEKS, positions, strict=True)
    ]


def test_every_check_is_declared_and_assessed_exactly_once():
    states, items = verdicts(healthy())
    assert set(states) == set(visibility.CHECKS)
    assert all(v["state"] == "clear" for v in states.values()), {
        k: v["reason"] for k, v in states.items() if v["state"] != "clear"
    }
    assert items == []
    health = analyze(healthy(), AS_OF)["location"]["health"]
    score = next(c for c in health["categories"] if c["category"] == "visibility")
    assert score["score"] == 100 and score["checks_passed"] == len(visibility.CHECKS)
    assert score["checks_not_evaluated"] == 0


def test_permanently_closed_suppresses_everything():
    snapshot = healthy()
    snapshot["locations"][0]["open_status"] = "closed_permanently"
    states, items = verdicts(snapshot)
    assert all(v["state"] == "suppressed" for v in states.values()) and items == []


def test_stale_or_missing_tracking_abstains_every_rank_check():
    # Four weeks after the last check: stale, but the monthly terms are still current.
    states, items = verdicts(healthy(), as_of=date(2026, 10, 5))
    assert states["tracking_stale"]["state"] == "triggered"
    assert all(states[r]["state"] == "insufficient_data" for r in visibility.RANK_RULES)
    assert [i["rule"] for i in items] == ["tracking_stale"]
    # Search-term checks do not depend on the tracker, so they still run.
    assert states["search_term_losing"]["state"] == "clear"
    assert (
        verdicts(healthy(), EngineConfig(rank_freshness_days=90), as_of=date(2026, 10, 5))[0][
            "tracking_stale"
        ]["state"]
        == "clear"
    )

    snapshot = healthy()
    snapshot["keywords"] = []
    states, _ = verdicts(snapshot)
    assert states["tracking_stale"]["state"] == "insufficient_data"
    assert all(states[r]["state"] == "insufficient_data" for r in visibility.RANK_RULES)


def test_pack_share_lost_and_drop_move_together():
    snapshot = healthy()
    set_ranks(snapshot, "k2", [2, 2, 2, 5])
    set_ranks(snapshot, "k3", [3, 3, 3, 6])
    states, items = verdicts(snapshot)
    by_rule = {}
    for item in items:
        by_rule.setdefault(item["rule"], []).append(item)
    # 1 of 4 in the pack is exactly the 25% floor, so the share is still fine.
    assert states["pack_share_low"]["state"] == "clear"
    assert states["pack_lost"]["state"] == "triggered"
    assert states["pack_lost"]["issues"] == 2 and states["pack_lost"]["evaluated"] == 4
    assert sorted(i["subject"] for i in by_rule["pack_lost"]) == [
        "dentist austin",
        "emergency dentist austin",
    ]
    assert states["rank_dropped"]["state"] == "triggered"
    assert sorted(i["subject"] for i in by_rule["rank_dropped"]) == [
        "dentist austin",
        "emergency dentist austin",
    ]
    assert by_rule["rank_dropped"][0]["evidence"][0]["values"]["earlier_mean"] == 2.0
    # One week in the band is not yet an opportunity.
    assert states["near_pack_opportunity"]["state"] == "clear"

    assert (
        verdicts(snapshot, EngineConfig(pack_share_min=0.5))[0]["pack_share_low"]["state"]
        == "triggered"
    )
    assert (
        verdicts(snapshot, EngineConfig(rank_drop_min_positions=4))[0]["rank_dropped"]["state"]
        == "clear"
    )


def test_near_pack_is_a_notice_level_opportunity():
    snapshot = healthy()
    set_ranks(snapshot, "k4", [6, 7, 10, 6])
    states, items = verdicts(snapshot)
    assert states["near_pack_opportunity"]["state"] == "triggered"
    assert states["near_pack_opportunity"]["evaluated"] == 4
    finding = next(i for i in items if i["rule"] == "near_pack_opportunity")
    assert finding["subject"] == "dentist open saturday austin"
    assert finding["severity"] == "notice"
    assert finding["evidence"][0]["values"]["weeks_near"] == [WEEKS[0], WEEKS[1], WEEKS[3]]
    assert (
        verdicts(snapshot, EngineConfig(near_pack_min_weeks=4))[0]["near_pack_opportunity"]["state"]
        == "clear"
    )


def test_not_found_must_be_consecutive_and_ends_in_the_latest_week():
    snapshot = healthy()
    set_ranks(snapshot, "k4", [None, None, None, None])
    states, items = verdicts(snapshot)
    assert states["not_found_persistent"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "not_found_persistent")
    assert finding["subject"] == "dentist open saturday austin"
    assert finding["severity"] == "warning"
    # Rank rules that need a position leave the unfound keyword out, never treat it as 0.
    assert states["rank_dropped"]["state"] == "clear"
    set_ranks(snapshot, "k4", [None, None, None, 12])
    assert verdicts(snapshot)[0]["not_found_persistent"]["state"] == "clear"
    set_ranks(snapshot, "k4", [12, None, None, None])
    assert (
        verdicts(snapshot, EngineConfig(not_found_min_weeks=3))[0]["not_found_persistent"]["state"]
        == "triggered"
    )


def test_high_intent_keywords_are_judged_against_the_rest():
    snapshot = healthy()
    set_ranks(snapshot, "k3", [3, 3, 3, 12])
    states, items = verdicts(snapshot)
    assert states["high_intent_lagging"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "high_intent_lagging")
    assert finding["subject"] == "emergency dentist austin"
    assert finding["evidence"][0]["values"]["baseline_median"] == 2
    set_ranks(snapshot, "k3", [3, 3, 3, None])
    finding = next(i for i in verdicts(snapshot)[1] if i["rule"] == "high_intent_lagging")
    assert "not found" in finding["why"] and finding["severity"] == "warning"
    assert (
        verdicts(snapshot, EngineConfig(high_intent_intents=("implants",)))[0][
            "high_intent_lagging"
        ]["state"]
        == "insufficient_data"
    )


def test_branded_keyword_must_rank_first():
    snapshot = healthy()
    set_ranks(snapshot, "k1", [1, 1, 1, 2])
    states, items = verdicts(snapshot)
    assert states["branded_not_first"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "branded_not_first")
    assert finding["subject"] == "brightpath dental austin" and finding["severity"] == "warning"
    set_ranks(snapshot, "k1", [1, 1, 1, None])
    finding = next(i for i in verdicts(snapshot)[1] if i["rule"] == "branded_not_first")
    assert finding["severity"] == "critical"
    # The city in a branch name is not a brand word.
    snapshot["locations"][0]["title"] = "Brightpath Dental Austin"
    assert verdicts(snapshot)[0]["branded_not_first"]["issues"] == 1
    snapshot["keywords"] = [k for k in snapshot["keywords"] if k["id"] != "k1"]
    assert verdicts(snapshot)[0]["branded_not_first"]["state"] == "insufficient_data"


def test_search_terms_pair_exact_months_only():
    snapshot = healthy()
    snapshot["search_terms"][1]["impressions"] = 200
    states, items = verdicts(snapshot)
    assert states["search_term_losing"]["state"] == "triggered"
    assert states["search_term_losing"]["issues"] == 1
    assert states["search_term_losing"]["evaluated"] == 3
    finding = next(i for i in items if i["rule"] == "search_term_losing")
    assert finding["subject"] == "dentist austin"
    assert finding["evidence"][0]["values"]["drop"] == 0.6
    # A threshold month is never paired, so the loss disappears from view.
    snapshot["search_terms"][0]["is_threshold"] = True
    assert verdicts(snapshot)[0]["search_term_losing"]["state"] == "clear"
    assert (
        verdicts(snapshot, EngineConfig(term_loss_min_impressions=400))[0]["search_term_losing"][
            "state"
        ]
        == "insufficient_data"
    )
    snapshot["search_terms"] = [term("2026-03", "dentist austin", 500)]
    states, _ = verdicts(snapshot)
    assert states["search_term_losing"]["state"] == "insufficient_data"
    assert states["service_not_surfacing"]["state"] == "insufficient_data"


def test_services_must_surface_in_search_terms():
    snapshot = healthy()
    snapshot["projects"][0]["services"].append("Dental implants")
    states, items = verdicts(snapshot)
    assert states["service_not_surfacing"]["state"] == "triggered"
    assert states["service_not_surfacing"]["evaluated"] == 3
    finding = next(i for i in items if i["rule"] == "service_not_surfacing")
    assert finding["subject"] == "Dental implants" and finding["severity"] == "notice"
    snapshot["projects"] = []
    assert verdicts(snapshot)[0]["service_not_surfacing"]["state"] == "insufficient_data"


def test_rivals_compared_within_keyword_and_week():
    snapshot = healthy()
    # Rival 0 ahead on three keywords with far more reviews and photos than our 100 / 40.
    for kid in ("k2", "k3", "k4"):
        snapshot["competitors"] = [
            c
            for c in snapshot["competitors"]
            if not (c["tracked_keyword_id"] == kid and c["competitor_name"] == "Rival 0")
        ] + [rival(kid, WEEKS[-1], "Rival 0", 1, reviews=300, rating=4.2, photos=90)]
    states, items = verdicts(snapshot)
    assert states["rival_ahead_gap"]["state"] == "triggered"
    finding = next(i for i in items if i["rule"] == "rival_ahead_gap")
    assert finding["subject"] == "Rival 0"
    values = finding["evidence"][0]["values"]
    assert values["gaps"] == {"reviews": 300, "photos": 90}
    assert values["ours"] == {"review_count": 100, "average_rating": 4.5, "photo_count": 40}
    assert len(values["keywords"]) == 3
    # Same rival, but only ahead in an older week: nothing to compare in the latest.
    for c in snapshot["competitors"]:
        if c["competitor_name"] == "Rival 0" and c["review_count"] == 300:
            c["week_start"] = WEEKS[0]
    assert verdicts(snapshot)[0]["rival_ahead_gap"]["state"] == "clear"
    snapshot["competitors"] = []
    assert verdicts(snapshot)[0]["rival_ahead_gap"]["state"] == "insufficient_data"


def test_card_summarises_the_tracker_view():
    snapshot = healthy()
    set_ranks(snapshot, "k4", [6, 7, None, 6])
    card = visibility.card(snapshot)
    assert card["latest_week"] == WEEKS[-1] and card["weeks"] == WEEKS
    assert card["keywords_tracked"] == 4 and card["in_pack"] == 3
    assert card["near_pack"] == 1 and card["not_found"] == 0
    assert card["best"] == {"keyword": "brightpath dental austin", "position": 1}
    assert card["worst"] == {"keyword": "dentist open saturday austin", "position": 6}
    assert card["keywords"][-1]["trend"] == [6, 7, None, 6]
    assert card["top_terms"][0]["term"] == "dentist austin"
    assert card["top_terms"][0]["change"] == 0.04
    assert card["rivals_ahead"][0]["keywords_ahead"] >= 1
    assert card["ours"]["review_count"] == 100
    report = analyze(snapshot, AS_OF)
    assert report["location"]["cards"]["visibility"]["pack_share"] == 0.75
