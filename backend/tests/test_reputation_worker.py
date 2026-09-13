"""Reputation worker: every check passes, fails, or abstains for the right reason.

Mutation tests: change one input, one verdict changes. Missing evidence abstains.
"""

from datetime import date, timedelta

from app.services.recommendations.categories import reputation
from app.services.recommendations.engine import analyze, run_worker
from app.services.recommendations.types import EngineConfig

AS_OF = date(2026, 9, 11)
LOC = "loc-1"

# Twenty-four reviews, one every eight days, newest one day old. Four are low (three
# 3-star, one 1-star), every one answered two days after it was posted.
LOW = {2: 3, 10: 3, 14: 1, 18: 3}


def review(i: int, rating: int | None = None, reply_days: int | None = 2) -> dict:
    created = AS_OF - timedelta(days=i * 8 + 1)
    return {
        "id": f"r-{i:02d}",
        "location_id": LOC,
        "google_review_id": f"g-{i:02d}",
        "is_anonymous": False,
        "star_rating": LOW.get(i, 5) if rating is None else rating,
        "comment": f"Visit number {i}: the hygienist was gentle and the wait was short.",
        "create_time": f"{created.isoformat()}T10:00:00+00:00",
        "update_time": f"{created.isoformat()}T10:00:00+00:00",
        "reply_comment": "Thank you for taking the time to share this."
        if reply_days is not None
        else None,
        "reply_update_time": (
            f"{(created + timedelta(days=reply_days)).isoformat()}T09:00:00+00:00"
            if reply_days is not None
            else None
        ),
    }


def complete() -> dict:
    """A profile whose reviews pass every check."""
    return {
        "locations": [
            {
                "id": LOC,
                "title": "Brightpath Dental",
                "source": "fixture",
                "primary_category_display": "Dentist",
                "locality": "Austin",
                "open_status": "open",
            }
        ],
        "reviews": [review(i) for i in range(24)],
        "keywords": [
            {"id": "k1", "location_id": LOC, "keyword": "dentist austin"},
            {"id": "k2", "location_id": LOC, "keyword": "emergency dentist"},
        ],
        "competitors": [
            {
                "id": "co-1",
                "tracked_keyword_id": "k1",
                "week_start": "2026-09-07",
                "competitor_name": "Park Dental",
                "review_count": 40,
                "average_rating": 4.4,
            },
            {
                "id": "co-2",
                "tracked_keyword_id": "k1",
                "week_start": "2026-09-07",
                "competitor_name": "Lake Dental",
                "review_count": 30,
                "average_rating": 4.1,
            },
            # An older week for the same keyword must not count.
            {
                "id": "co-3",
                "tracked_keyword_id": "k1",
                "week_start": "2026-08-31",
                "competitor_name": "Park Dental",
                "review_count": 400,
                "average_rating": 4.4,
            },
            {
                "id": "co-4",
                "tracked_keyword_id": "k2",
                "week_start": "2026-09-07",
                "competitor_name": "Night Dental",
                "review_count": 36,
                "average_rating": 4.0,
            },
        ],
        "projects": [
            {
                "id": "p1",
                "name": "Brightpath Dental Group",
                "website_url": "https://example.org",
                "description": "Family dental group.",
                "services": ["Routine cleaning", "Teeth whitening"],
            }
        ],
    }


def verdicts(snapshot, config=None):
    result = run_worker(snapshot, AS_OF, config or EngineConfig(), "reputation")
    return {e["rule"]: e for e in result["evaluations"]}, result["items"]


def finding(items, rule):
    return next(i for i in items if i["rule"] == rule)


def test_every_check_is_declared_and_assessed_exactly_once():
    states, items = verdicts(complete())
    assert set(states) == set(reputation.CHECKS)
    assert all(v["state"] == "clear" for v in states.values()), {
        k: v["reason"] for k, v in states.items() if v["state"] != "clear"
    }
    assert items == []
    health = analyze(complete(), AS_OF)["location"]["health"]
    score = next(c for c in health["categories"] if c["category"] == "reputation")
    assert score["score"] == 100 and score["checks_passed"] == len(reputation.CHECKS)
    assert score["checks_not_evaluated"] == 0


def test_permanently_closed_suppresses_everything():
    snapshot = complete()
    snapshot["locations"][0]["open_status"] = "closed_permanently"
    states, items = verdicts(snapshot)
    assert all(v["state"] == "suppressed" for v in states.values()) and items == []


def test_no_reviews_abstains_rather_than_scoring_zero():
    snapshot = complete()
    snapshot["reviews"] = []
    states, items = verdicts(snapshot)
    # Zero stored rows against a competitor benchmark is the one thing that still fires.
    assert [i["rule"] for i in items] == ["reviews_few_vs_competitors"]
    for rule in reputation.CHECKS:
        if rule != "reviews_few_vs_competitors":
            assert states[rule]["state"] == "insufficient_data", rule


def test_rating_low_is_warning_then_critical_and_abstains_when_thin():
    snapshot = complete()
    for r in snapshot["reviews"][:6]:
        r["star_rating"] = 3
    states, items = verdicts(snapshot)
    assert states["rating_low"]["state"] == "triggered"
    assert finding(items, "rating_low")["severity"] == "warning"
    assert finding(items, "rating_low")["evidence"][0]["values"]["average"] < 4

    for r in snapshot["reviews"][:12]:
        r["star_rating"] = 1
    states, items = verdicts(snapshot)
    assert finding(items, "rating_low")["severity"] == "critical"

    snapshot = complete()
    snapshot["reviews"] = snapshot["reviews"][:3] + snapshot["reviews"][12:]
    assert verdicts(snapshot)[0]["rating_low"]["state"] == "insufficient_data"


def test_null_star_rating_is_invalid_not_zero():
    snapshot = complete()
    for r in snapshot["reviews"][:11]:
        r["star_rating"] = None
    states, _ = verdicts(snapshot)
    # One rated review left in the window: abstain rather than average a None.
    assert states["rating_low"]["state"] == "insufficient_data"
    # Volume still counts the rows.
    assert states["reviews_few_vs_competitors"]["state"] == "clear"
    assert reputation.stars({"star_rating": True}) is None
    assert reputation.stars({"star_rating": 7}) is None


def test_one_star_share():
    snapshot = complete()
    for r in snapshot["reviews"][:5]:
        r["star_rating"] = 1
    states, items = verdicts(snapshot)
    assert states["one_star_share_high"]["state"] == "triggered"
    assert finding(items, "one_star_share_high")["evidence"][0]["values"]["one_star"] == 6
    assert (
        verdicts(snapshot, EngineConfig(one_star_share_max=0.5))[0]["one_star_share_high"]["state"]
        == "clear"
    )


def test_rating_trend_falling():
    snapshot = complete()
    for r in snapshot["reviews"]:
        r["star_rating"] = 5
    for r in snapshot["reviews"][:12]:
        r["star_rating"] = 4
    states, items = verdicts(snapshot)
    assert states["rating_trend_falling"]["state"] == "triggered"
    values = finding(items, "rating_trend_falling")["evidence"][0]["values"]
    assert values["prior_average"] == 5 and values["recent_average"] == 4
    # A rise is never a finding.
    for r in snapshot["reviews"][:12]:
        r["star_rating"] = 5
    for r in snapshot["reviews"][12:]:
        r["star_rating"] = 3
    assert verdicts(snapshot)[0]["rating_trend_falling"]["state"] == "clear"
    # Thin prior window abstains.
    snapshot["reviews"] = snapshot["reviews"][:14]
    assert verdicts(snapshot)[0]["rating_trend_falling"]["state"] == "insufficient_data"


def test_review_count_versus_competitors_uses_latest_week_only():
    snapshot = complete()
    states, _ = verdicts(snapshot)
    assert states["reviews_few_vs_competitors"]["state"] == "clear"
    for row in snapshot["competitors"]:
        row["review_count"] = 300
    states, items = verdicts(snapshot)
    assert states["reviews_few_vs_competitors"]["state"] == "triggered"
    values = finding(items, "reviews_few_vs_competitors")["evidence"][0]["values"]
    assert values["competitor_median"] == 300 and values["stored_reviews"] == 24
    assert "co-3" not in finding(items, "reviews_few_vs_competitors")["evidence"][0]["row_ids"]
    assert finding(items, "reviews_few_vs_competitors")["confidence"] == "medium"
    for row in snapshot["competitors"]:
        row["review_count"] = None
    assert verdicts(snapshot)[0]["reviews_few_vs_competitors"]["state"] == "insufficient_data"
    snapshot["competitors"] = []
    assert verdicts(snapshot)[0]["reviews_few_vs_competitors"]["state"] == "insufficient_data"


def test_recency_and_velocity():
    snapshot = complete()
    snapshot["reviews"] = snapshot["reviews"][4:]
    states, items = verdicts(snapshot)
    assert states["no_recent_review"]["state"] == "triggered"
    assert finding(items, "no_recent_review")["evidence"][0]["values"]["days_since_last"] == 33
    assert states["review_velocity_low"]["state"] == "triggered"
    assert finding(items, "review_velocity_low")["evidence"][0]["values"]["last_30_days"] == 0
    assert (
        verdicts(snapshot, EngineConfig(review_gap_max_days=60))[0]["no_recent_review"]["state"]
        == "clear"
    )


def test_reply_rate_overall_and_on_low_reviews():
    snapshot = complete()
    for r in snapshot["reviews"][4:20]:
        r["reply_comment"] = None
        r["reply_update_time"] = None
    states, items = verdicts(snapshot)
    assert states["reply_rate_low"]["state"] == "triggered"
    assert states["reply_rate_low"]["evaluated"] == 23  # the one-day-old review is excluded
    assert finding(items, "reply_rate_low")["evidence"][0]["values"]["answered"] == 7
    assert states["critical_reply_rate_low"]["state"] == "triggered"
    assert finding(items, "critical_reply_rate_low")["evidence"][0]["values"]["answered"] == 1
    # A blank reply is no reply.
    snapshot = complete()
    for r in snapshot["reviews"][1:22]:
        r["reply_comment"] = "  "
    assert verdicts(snapshot)[0]["reply_rate_low"]["state"] == "triggered"
    # Thin evidence abstains.
    snapshot = complete()
    snapshot["reviews"] = snapshot["reviews"][:4]
    states, _ = verdicts(snapshot)
    assert states["reply_rate_low"]["state"] == "insufficient_data"
    assert states["critical_reply_rate_low"]["state"] == "insufficient_data"


def test_unanswered_low_reviews_are_enumerated_by_review_id():
    snapshot = complete()
    for r in snapshot["reviews"]:
        if r["id"] in ("r-10", "r-14"):
            r["reply_comment"] = ""
            r["reply_update_time"] = None
    states, items = verdicts(snapshot)
    assert states["critical_review_unanswered"]["state"] == "triggered"
    assert states["critical_review_unanswered"]["issues"] == 2
    assert states["critical_review_unanswered"]["evaluated"] == 4
    waiting = [i for i in items if i["rule"] == "critical_review_unanswered"]
    assert [w["subject"] for w in waiting] == ["g-10", "g-14"]  # newest first
    assert waiting[1]["severity"] == "critical" and "1-star" in waiting[1]["title"]
    assert "hygienist" in waiting[0]["why"]
    assert all("reviewer" not in w["why"].lower() for w in waiting)
    # The list is capped; the verdict still counts every one.
    states, items = verdicts(snapshot, EngineConfig(unanswered_list_max=1))
    assert states["critical_review_unanswered"]["issues"] == 2
    assert len([i for i in items if i["rule"] == "critical_review_unanswered"]) == 1
    # A low review younger than the wait is not yet expected to have a reply.
    snapshot = complete()
    snapshot["reviews"][0]["star_rating"] = 2
    snapshot["reviews"][0]["reply_comment"] = None
    assert verdicts(snapshot)[0]["critical_review_unanswered"]["state"] == "clear"
    # No low review at all: nothing to judge.
    for r in snapshot["reviews"]:
        r["star_rating"] = 5
    assert verdicts(snapshot)[0]["critical_review_unanswered"]["state"] == "insufficient_data"


def test_reply_delay_median():
    snapshot = complete()
    snapshot["reviews"] = [review(i, reply_days=12) for i in range(24)]
    states, items = verdicts(snapshot)
    assert states["reply_delay_high"]["state"] == "triggered"
    assert finding(items, "reply_delay_high")["evidence"][0]["values"]["median_days"] == 12
    # Replies without a date cannot be timed.
    for r in snapshot["reviews"]:
        r["reply_update_time"] = None
    assert verdicts(snapshot)[0]["reply_delay_high"]["state"] == "insufficient_data"


def test_score_falls_with_severity():
    snapshot = complete()
    for r in snapshot["reviews"][:12]:
        r["star_rating"] = 1
    critical = analyze(snapshot, AS_OF)["location"]["health"]["score"]
    snapshot = complete()
    snapshot["reviews"] = [review(i, reply_days=9) for i in range(24)]
    notice = analyze(snapshot, AS_OF)["location"]["health"]["score"]
    assert critical < notice < 100
    for item in run_worker(snapshot, AS_OF, EngineConfig(), "reputation")["items"]:
        assert item["evidence"] and item["why"] and item["action"]


def test_card_and_summary_fallback():
    from app.services.recommendations.suggestions.reputation import fallback_summary

    snapshot = complete()
    snapshot["reviews"][14]["reply_comment"] = None
    snapshot["reviews"][3]["star_rating"] = None
    card = reputation.card(snapshot)
    assert card["count"] == 24 and card["rated_count"] == 23
    assert card["distribution"] == {"5": 19, "4": 0, "3": 3, "2": 0, "1": 1}
    assert card["replied_share"] == round(23 / 24, 3) and card["median_reply_days"] == 2
    assert card["last_review_date"] == "2026-09-10"
    assert card["unanswered_critical_count"] == 1
    assert card["unanswered"][0]["id"] == "g-14" and card["unanswered"][0]["rating"] == 1
    assert len(card["unanswered"][0]["comment"]) <= 141
    assert "reviewer" not in str(card)

    report = analyze(snapshot, AS_OF)["location"]
    assert report["cards"]["reputation"]["unanswered_critical_count"] == 1
    assert all(row["group"] and row["effort"] for row in report["by_rule"])
    summary = fallback_summary(run_worker(snapshot, AS_OF, EngineConfig(), "reputation"))
    assert summary["source"] == "deterministic" and "Fix first" in summary["text"]
    assert "passed" in fallback_summary({"items": []})["text"]
