"""Health scoring, exhaustive enumeration and metric availability."""

from datetime import timedelta

from test_recommendations import AS_OF, data

from app.services.recommendations.engine import analyze, compare
from app.services.recommendations.types import EngineConfig

WEEKS = [AS_OF - timedelta(days=AS_OF.weekday() + 1 + 7 * i) for i in range(4)]


def category(report, location_index=0, name="visibility"):
    categories = report["locations"][location_index]["health"]["categories"]
    return next(c for c in categories if c["category"] == name)


def keyword_snapshot(failing: int, passing: int):
    """Keywords with four consecutive fresh weekly checks; `failing` miss the pack."""
    snapshot = data()
    snapshot["keywords"] = [
        {"id": f"k{i}", "location_id": "location-x", "keyword": f"term {i}", "device": "mobile"}
        for i in range(failing + passing)
    ]
    snapshot["ranks"] = [
        {
            "id": f"k{i}-{w}",
            "location_id": "location-x",
            "tracked_keyword_id": f"k{i}",
            "week_start": str(week),
            "found": True,
            "rank_absolute": 12 if i < failing else 2,
            "rank_in_local_pack": None if i < failing else 2,
        }
        for i in range(failing + passing)
        for w, week in enumerate(WEEKS)
    ]
    return snapshot


def test_unevaluated_checks_are_excluded_from_the_score_not_counted_as_passes():
    health = analyze(data(), AS_OF)["locations"][0]["health"]
    assert health["checks_passed"] == 1 and health["checks_failed"] == 1
    assert health["checks_not_evaluated"] == 8
    assert health["coverage"] == 0.2
    # Only the two evaluated categories carry weight; the other four score None and are
    # left out of the weighted mean rather than silently counted as passing.
    scored = [c for c in health["categories"] if c["score"] is not None]
    assert {c["category"] for c in scored} == {"profile", "reputation"}
    assert health["score"] == 50 and health["grade"] == "fair"
    assert all(c["checks_not_evaluated"] for c in health["categories"] if c["score"] is None)


def test_abstaining_on_more_checks_never_raises_the_score():
    snapshot = data()
    baseline = analyze(snapshot, AS_OF)["locations"][0]["health"]
    snapshot["media"] = [{"id": "m", "location_id": "location-x", "has_cover_photo": None}]
    widened = analyze(snapshot, AS_OF)["locations"][0]["health"]
    assert widened["score"] == baseline["score"]
    assert widened["checks_not_evaluated"] == baseline["checks_not_evaluated"]


def test_every_failing_keyword_is_reported_with_a_stable_identifying_key():
    report = analyze(keyword_snapshot(failing=3, passing=2), AS_OF)
    items = [r for r in report["items"] if r["rule"] == "rankings"]
    assert len(items) == 3
    assert {r["subject"] for r in items} == {"term 0", "term 1", "term 2"}
    assert len({r["key"] for r in items}) == 3
    assert all(r["key"] == f"location-x:rankings:{r['subject']}" for r in items)
    verdict = next(e for e in report["evaluations"] if e["rule"] == "rankings")
    assert verdict["state"] == "triggered"
    assert verdict["issues"] == 3 and verdict["evaluated"] == 5
    # Exactly one coverage verdict per rule even though the rule emitted many findings.
    assert sum(e["rule"] == "rankings" for e in report["evaluations"]) == 1


def test_a_wide_failure_scores_worse_than_a_narrow_one_at_the_same_severity():
    narrow = analyze(keyword_snapshot(failing=2, passing=8), AS_OF)
    wide = analyze(keyword_snapshot(failing=9, passing=1), AS_OF)
    assert {r["severity"] for r in narrow["items"] if r["rule"] == "rankings"} == {
        r["severity"] for r in wide["items"] if r["rule"] == "rankings"
    }
    assert category(narrow)["score"] > category(wide)["score"]
    # Tracking more keywords must not by itself lower the score.
    assert (
        category(analyze(keyword_snapshot(2, 8), AS_OF))["score"]
        == category(analyze(keyword_snapshot(4, 16), AS_OF))["score"]
    )


def test_settled_outcomes_read_a_longer_window_than_the_daily_comparisons():
    snapshot = data()
    snapshot["bookings"] = [
        {
            "id": f"b{i}",
            "location_id": "location-x",
            "booking_created_at": str(AS_OF - timedelta(days=85)),
            "requested_for_date": str(AS_OF - timedelta(days=80 - 3 * i)),
            "status": "no_show" if i < 10 else "completed",
        }
        for i in range(25)
    ]
    item = next(r for r in analyze(snapshot, AS_OF)["items"] if r["rule"] == "booking_outcomes")
    assert item["evidence"][0]["values"]["settled"] == 25
    assert item["evidence"][0]["values"]["window_days"] == 90
    # A 28-day outcome window cannot reach a denominator worth reporting and must abstain.
    narrow = analyze(snapshot, AS_OF, EngineConfig(outcome_window_days=28))
    verdict = next(e for e in narrow["evaluations"] if e["rule"] == "booking_outcomes")
    assert verdict["state"] == "insufficient_data"
    assert not any(r["rule"] == "booking_outcomes" for r in narrow["items"])


def performance_snapshot(before: int, now: int):
    from app.services.recommendations.performance import ACTIONS, IMPRESSIONS

    snapshot = data()
    snapshot["performance"] = [
        {
            "id": f"p{i}",
            "location_id": "location-x",
            "date": str(AS_OF - timedelta(days=i)),
            **{key: (now if i < 28 else before) for key in IMPRESSIONS},
            **{key: (now if i < 28 else before) for key in ACTIONS},
        }
        for i in range(56)
    ]
    return snapshot


def test_severity_tiers_separate_a_small_decline_from_a_collapse():
    small = analyze(performance_snapshot(before=100, now=88), AS_OF)
    large = analyze(performance_snapshot(before=100, now=30), AS_OF)
    assert next(r for r in small["items"] if r["rule"] == "performance")["severity"] == "notice"
    assert next(r for r in large["items"] if r["rule"] == "performance")["severity"] == "critical"
    assert (
        category(small, name="performance")["score"] > category(large, name="performance")["score"]
    )
    # Below the reporting floor the check passes rather than producing a finding.
    flat = analyze(performance_snapshot(before=100, now=98), AS_OF)
    assert next(e for e in flat["evaluations"] if e["rule"] == "performance")["state"] == "clear"
    assert category(flat, name="performance")["score"] == 100


def test_metrics_report_unavailable_rather_than_zero():
    report = analyze(data(), AS_OF)
    metrics = {m["key"]: m for m in report["locations"][0]["metrics"]}
    assert metrics["impressions"]["available"] is False
    assert metrics["impressions"]["value"] is None
    assert metrics["average_rating"]["value"] == 2
    assert metrics["unanswered_critical"]["value"] == 5
    assert metrics["reply_rate"]["value"] == 0.0
    assert all(m["basis"] for m in report["locations"][0]["metrics"])


def test_metrics_measure_change_against_the_previous_window():
    report = analyze(performance_snapshot(before=100, now=50), AS_OF)
    metrics = {m["key"]: m for m in report["locations"][0]["metrics"]}
    assert metrics["impressions"]["value"] == 28 * 4 * 50
    assert metrics["impressions"]["previous"] == 28 * 4 * 100
    assert metrics["impressions"]["change_pct"] == -0.5
    assert metrics["impressions"]["direction"] == "up_is_good"


def test_fleet_rollup_clusters_issues_and_tracks_the_score_between_runs():
    report = analyze(keyword_snapshot(failing=3, passing=2), AS_OF)
    health = report["health"]
    assert health["locations_scored"] == 1 and health["locations_total"] == 1
    rankings = next(r for r in health["by_rule"] if r["rule"] == "rankings")
    assert rankings["issues"] == 3 and rankings["locations_affected"] == 1
    visibility = next(c for c in health["by_category"] if c["category"] == "visibility")
    assert visibility["issues"] == 3 and visibility["weight"] == 25
    assert sum(health["severity"].values()) == len(report["items"])
    assert health["worst_locations"][0]["score"] == report["locations"][0]["health"]["score"]

    improved = analyze(keyword_snapshot(failing=1, passing=4), AS_OF)
    compare(improved, report)
    assert improved["health"]["previous_score"] == health["score"]
    assert improved["health"]["score_change"] > 0


def test_check_inventory_lists_passing_and_unevaluated_checks_not_only_failures():
    report = analyze(keyword_snapshot(failing=3, passing=2), AS_OF)
    inventory = {row["rule"]: row for row in report["health"]["by_rule"]}
    # Every check the engine can run appears, so the issues view can reveal a check that
    # passed instead of leaving the reader unable to tell it apart from one that failed.
    assert len(inventory) == 10
    rankings = inventory["rankings"]
    assert rankings["issues"] == 3
    assert rankings["subjects_failed"] == 3 and rankings["subjects_examined"] == 5
    assert rankings["unit"] == "keyword" and rankings["predicate"]
    profile = inventory["profile"]
    assert profile["issues"] == 0 and profile["locations_passed"] == 1
    assert profile["worst_severity"] is None and profile["max_score"] == 0
    media = inventory["media"]
    assert media["issues"] == 0 and media["locations_not_evaluated"] == 1
    assert all(row["label"] and row["checks"] and row["fix"] for row in inventory.values())


def test_each_location_carries_its_own_check_inventory():
    snapshot = keyword_snapshot(failing=2, passing=3)
    snapshot["locations"].append(
        {**snapshot["locations"][0], "id": "location-y", "title": "A quiet business"}
    )
    report = analyze(snapshot, AS_OF)
    quiet = next(loc for loc in report["locations"] if loc["id"] == "location-y")
    busy = next(loc for loc in report["locations"] if loc["id"] == "location-x")
    assert len(quiet["by_rule"]) == len(busy["by_rule"]) == 10
    # The second location has no keywords of its own, so its rankings check abstains
    # rather than inheriting the first location's findings.
    quiet_rankings = next(r for r in quiet["by_rule"] if r["rule"] == "rankings")
    busy_rankings = next(r for r in busy["by_rule"] if r["rule"] == "rankings")
    assert busy_rankings["issues"] == 2 and busy_rankings["subjects_examined"] == 5
    assert quiet_rankings["issues"] == 0
    assert quiet_rankings["state"] == "insufficient_data" and quiet_rankings["reason"]
    # A single-location inventory names one verdict; the fleet one cannot.
    assert next(r for r in report["health"]["by_rule"] if r["rule"] == "rankings")["state"] is None


def test_each_location_carries_its_own_change_since_the_previous_audit():
    """The delta rides on the report, so no earlier audit needs to be kept."""
    first = analyze(keyword_snapshot(failing=4, passing=1), AS_OF)
    second = analyze(keyword_snapshot(failing=1, passing=4), AS_OF)
    compare(second, first)
    location = second["locations"][0]
    assert location["health"]["previous_score"] == first["locations"][0]["health"]["score"]
    assert location["health"]["score_change"] > 0
    # A location the earlier audit never saw reports no comparison rather than a fake one.
    fresh = analyze(keyword_snapshot(failing=1, passing=4), AS_OF)
    compare(fresh, {"health": {}, "items": [], "locations": [], "evaluations": []})
    assert fresh["locations"][0]["health"]["previous_score"] is None
    assert fresh["locations"][0]["health"]["score_change"] is None
