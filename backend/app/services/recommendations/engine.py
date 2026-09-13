"""Pure function: same snapshot, date and policy produce the same findings."""

from datetime import date

from app.services.recommendations.context import Context
from app.services.recommendations.metrics import collect
from app.services.recommendations.operations import evaluate_operations
from app.services.recommendations.performance import evaluate_performance, evaluate_search
from app.services.recommendations.policy import CATEGORIES
from app.services.recommendations.profile import evaluate_profile
from app.services.recommendations.rankings import evaluate_rankings
from app.services.recommendations.scoring import check_inventory, score_location, summarize
from app.services.recommendations.snapshot import fingerprint
from app.services.recommendations.types import ENGINE_VERSION, EngineConfig

SEVERITY_RANK = {"critical": 0, "warning": 1, "notice": 2}


def analyze(snapshot: dict, as_of: date, config: EngineConfig | None = None) -> dict:
    config = config or EngineConfig()
    items, evaluations, locations = [], [], []
    for location in snapshot.get("locations", []):
        c = Context(snapshot, location, as_of, config)
        evaluate_profile(c)
        evaluate_operations(c)
        evaluate_performance(c)
        evaluate_search(c)
        evaluate_rankings(c)
        found = [item.model_dump(mode="json") for item in c.items]
        verdicts = [item.model_dump(mode="json") for item in c.evaluations]
        items.extend(found)
        evaluations.extend(verdicts)
        locations.append(
            {
                "id": location["id"],
                "name": location["title"],
                "source_location_id": location.get("source_location_id"),
                "source": location.get("source"),
                "count": len(found),
                "health": score_location(location["id"], verdicts, found).model_dump(mode="json"),
                "metrics": [m.model_dump(mode="json") for m in collect(c)],
                # Each location carries its own check inventory so a single-location audit
                # never has to re-derive it from the fleet-wide lists.
                "by_rule": list(check_inventory(found, verdicts).values()),
            }
        )
    items.sort(key=lambda r: (-r["score"], r["location_name"], r["key"]))
    locations.sort(
        key=lambda loc: (loc["health"]["score"] is None, loc["health"]["score"] or 0, loc["name"])
    )
    return {
        "engine_version": ENGINE_VERSION,
        "as_of": as_of.isoformat(),
        "config": config.model_dump(),
        "fingerprint": fingerprint(snapshot),
        "health": summarize(locations, items, evaluations),
        "categories": [
            {"category": name, "label": spec["label"], "weight": spec["weight"]}
            for name, spec in CATEGORIES.items()
        ],
        "locations": locations,
        "items": items,
        "evaluations": evaluations,
        "counts": {key: len(rows) for key, rows in snapshot.items()},
        "explanation_source": "deterministic",
        "changes": [],
        "limitations": [
            "The health score is a versioned operating policy, not predicted revenue or uplift.",
            "Checks without enough evidence are excluded from the score, never scored as passes.",
            "As-of selects dated observations; profiles, replies and statuses are current state.",
            "Event recency cannot prove that an external feed is complete.",
            "Review text is not classified by an LLM in this version.",
        ],
    }


def compare(current: dict, previous: dict | None) -> None:
    if not previous:
        return
    old = {r["key"]: r for r in previous["items"]}
    now = {r["key"]: r for r in current["items"]}
    states = {(e["location_id"], e["rule"]): e["state"] for e in current["evaluations"]}
    for key, item in now.items():
        prior = old.get(key)
        if prior:
            fields = ("score", "evidence", "action", "confidence")
            item["change"] = (
                "unchanged" if all(prior.get(f) == item[f] for f in fields) else "changed"
            )
    for key, item in old.items():
        if key not in now:
            state = states.get((item["location_id"], item["rule"]), "insufficient_data")
            current["changes"].append(
                {
                    "key": key,
                    "location_name": item["location_name"],
                    "title": item["title"],
                    "change": "cannot_evaluate"
                    if state == "insufficient_data"
                    else "no_longer_triggered",
                    "reason": state,
                }
            )

    def delta(before, after):
        return after - before if isinstance(before, int) and isinstance(after, int) else None

    before = previous.get("health", {}).get("score")
    current["health"]["previous_score"] = before
    current["health"]["score_change"] = delta(before, current["health"]["score"])
    # Carried on the report itself, so "since the last audit" survives without keeping
    # the previous audit around to compare against later.
    prior_locations = {loc["id"]: loc for loc in previous.get("locations", [])}
    for location in current["locations"]:
        prior = prior_locations.get(location["id"], {}).get("health", {})
        location["health"]["previous_score"] = prior.get("score")
        location["health"]["score_change"] = delta(prior.get("score"), location["health"]["score"])
