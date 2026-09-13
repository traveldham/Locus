"""Audit the checked-in assignment deliverable, not just synthetic test inputs."""

import json
from datetime import date
from pathlib import Path

from app.services.recommendations.contracts import EXCLUDED
from app.services.recommendations.performance import ACTIONS, IMPRESSIONS


def test_saved_assignment_report_evidence_and_calculations():
    output = Path(__file__).resolve().parents[2] / "locus-intelligence-assignment" / "output"
    report = json.loads((output / "recommendations.json").read_text())
    evidence = json.loads((output / "evidence.json").read_text())
    assert {loc["source_location_id"] for loc in report["locations"]} == {
        f"LOC-{i:03}" for i in range(1, 13)
    }
    assert len(report["evaluations"]) == 120
    assert len({r["key"] for r in report["items"]}) == len(report["items"])
    indexed = {source: {r["id"]: r for r in rows} for source, rows in evidence.items()}
    as_of = date.fromisoformat(report["as_of"])
    for item in report["items"]:
        assert item["why"] and item["action"] and item["limitation"] and item["evidence"]
        for entry in item["evidence"]:
            rows = [indexed[entry["source"]][key] for key in entry["row_ids"]]
            assert all(not (set(row) & EXCLUDED) for row in rows)
            assert all(
                row.get("location_id", item["location_id"]) == item["location_id"] for row in rows
            )
            values = entry["values"]
            if item["rule"] == "reviews":
                pending = [
                    r
                    for r in rows
                    if r["star_rating"] <= 3
                    and not r["reply_comment"]
                    and (as_of - date.fromisoformat(r["create_time"][:10])).days
                    >= values["wait_days"]
                ]
                assert len(pending) == values["unanswered"]
                assert len(rows) == values["recent_reviews"]
            if item["rule"] == "performance":
                for period in ("current", "previous"):
                    subset = [
                        r
                        for r in rows
                        if values[f"{period}_start"] <= r["date"] <= values[f"{period}_end"]
                    ]
                    assert len(subset) == values["matched_days"]
                    assert (
                        sum(r[k] for r in subset for k in IMPRESSIONS)
                        == values[f"{period}_impressions"]
                    )
                    assert sum(r[k] for r in subset for k in ACTIONS) == values[f"{period}_actions"]
            if item["rule"] == "rankings" and entry["source"] == "ranks":
                assert sum(r["rank_in_local_pack"] is None for r in rows) == values["outside_pack"]
            if item["rule"] == "search":
                assert len(rows) == 2 and rows[0]["search_term"] == rows[1]["search_term"]
                assert sorted(r["impressions"] for r in rows) == sorted(
                    [values["previous"], values["current"]]
                )


def test_saved_assignment_report_scores_every_location_it_can_evaluate():
    output = Path(__file__).resolve().parents[2] / "locus-intelligence-assignment" / "output"
    report = json.loads((output / "recommendations.json").read_text())
    health = report["health"]
    weights = {c["category"]: c["weight"] for c in report["categories"]}
    assert sum(weights.values()) == 100
    assert 0 <= health["score"] <= 100
    assert sum(health["severity"].values()) == len(report["items"])

    for location in report["locations"]:
        score = location["health"]
        checks = score["checks_passed"] + score["checks_failed"] + score["checks_not_evaluated"]
        assert checks == sum(e["location_id"] == location["id"] for e in report["evaluations"])
        # A category is scored only where a check actually ran, and a scored category
        # with no failed check must be full marks: abstention never earns credit.
        for row in score["categories"]:
            if row["checks_passed"] + row["checks_failed"] == 0:
                assert row["score"] is None
            elif row["checks_failed"] == 0:
                assert row["score"] == 100
        scored = [c for c in score["categories"] if c["score"] is not None]
        assert score["score"] == round(
            sum(c["score"] * c["weight"] for c in scored) / sum(c["weight"] for c in scored)
        )
        assert score["issues"] == sum(r["location_id"] == location["id"] for r in report["items"])
        assert all(m["value"] is None for m in location["metrics"] if not m["available"])

    for verdict in report["evaluations"]:
        found = [
            r
            for r in report["items"]
            if r["location_id"] == verdict["location_id"] and r["rule"] == verdict["rule"]
        ]
        assert bool(found) == (verdict["state"] == "triggered")
        assert verdict["issues"] >= len(found)
    # Rules that enumerate must give every finding its own subject, or history cannot
    # tell one affected keyword from another between runs.
    for rule in ("rankings", "search"):
        assert all(r["subject"] for r in report["items"] if r["rule"] == rule)
