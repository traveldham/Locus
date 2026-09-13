"""Pure functions: same snapshot, date and policy produce the same report.

An audit is one pipeline of six workers. `run_worker` is what one worker computes on
its own; `assemble` is what the pipeline does once all six have reported.
"""

from datetime import date

from app.services.recommendations.categories import WORKERS, worker_for
from app.services.recommendations.context import Context
from app.services.recommendations.policy import CATEGORIES, RULE_DOCS
from app.services.recommendations.scoring import check_inventory, score_location
from app.services.recommendations.snapshot import fingerprint
from app.services.recommendations.types import ENGINE_VERSION, EngineConfig

SEVERITY_RANK = {"critical": 0, "warning": 1, "notice": 2}
EFFORT_RANK = {"minutes": 0, "hour": 1, "afternoon": 2}


def priorities(items: list[dict], limit: int = 5) -> list[str]:
    """The few findings to do first: one per check, worst severity first, drafts and
    quick fixes ahead of the rest, and no category taking more than two slots while
    another still has something to say. Keys, so the UI can look the findings up."""
    ranked = sorted(
        items,
        key=lambda i: (
            SEVERITY_RANK[i["severity"]],
            0 if i.get("suggestion") else 1,
            EFFORT_RANK.get(RULE_DOCS.get(i["rule"], {}).get("effort", "hour"), 1),
            -i["score"],
            i["key"],
        ),
    )
    chosen: list[dict] = []
    seen_rules: set[str] = set()
    per_category: dict[str, int] = {}
    # First pass: one per check, at most two per category.
    for item in ranked:
        if item["rule"] in seen_rules or per_category.get(item["category"], 0) >= 2:
            continue
        chosen.append(item)
        seen_rules.add(item["rule"])
        per_category[item["category"]] = per_category.get(item["category"], 0) + 1
        if len(chosen) == limit:
            break
    # Second pass: fill remaining slots with other checks regardless of category.
    for item in ranked:
        if len(chosen) == limit:
            break
        if item["rule"] not in seen_rules:
            chosen.append(item)
            seen_rules.add(item["rule"])
    return [i["key"] for i in chosen[:limit]]


def run_worker(snapshot: dict, as_of: date, config: EngineConfig, category: str) -> dict:
    """One category's findings and verdicts for the single profile in the snapshot."""
    location = snapshot["locations"][0]
    c = Context(snapshot, location, as_of, config)
    worker_for(category).evaluate(c)
    return {
        "category": category,
        "items": [item.model_dump(mode="json") for item in c.items],
        "evaluations": [verdict.model_dump(mode="json") for verdict in c.evaluations],
    }


def assemble(snapshot: dict, as_of: date, config: EngineConfig, results: list[dict]) -> dict:
    """Score the six workers' results into the profile's report."""
    location = snapshot["locations"][0]
    by_category = {result["category"]: result for result in results}
    items = [item for worker in WORKERS for item in by_category[worker.KEY]["items"]]
    evaluations = [e for worker in WORKERS for e in by_category[worker.KEY]["evaluations"]]
    items.sort(key=lambda r: (-r["score"], r["key"]))
    return {
        "engine_version": ENGINE_VERSION,
        "as_of": as_of.isoformat(),
        "config": config.model_dump(),
        "fingerprint": fingerprint(snapshot),
        "categories": [
            {"category": name, "label": spec["label"], "weight": spec["weight"]}
            for name, spec in CATEGORIES.items()
        ],
        "location": {
            "id": location["id"],
            "name": location["title"],
            "source_location_id": location.get("source_location_id"),
            "source": location.get("source"),
            "count": len(items),
            "health": score_location(evaluations, items).model_dump(mode="json"),
            "by_rule": check_inventory(items, evaluations),
            "priorities": priorities(items),
            # What each worker wants shown beside its findings: the profile card, a
            # summary. Workers that have not built these leave them out.
            "cards": {
                worker.KEY: worker.card(snapshot) for worker in WORKERS if hasattr(worker, "card")
            },
            "summaries": {
                result["category"]: result["summary"] for result in results if result.get("summary")
            },
            "suggestions": {
                result["category"]: result["suggestions"]
                for result in results
                if result.get("suggestions")
            },
        },
        "items": items,
        "evaluations": evaluations,
        "counts": {key: len(rows) for key, rows in snapshot.items()},
        "explanation_source": "deterministic",
        "limitations": [
            "The health score is a versioned operating policy, not predicted revenue or uplift.",
            "Checks without enough evidence are excluded from the score, never scored as passes.",
            "As-of selects dated observations; profiles, replies and statuses are current state.",
        ],
    }


def analyze(snapshot: dict, as_of: date, config: EngineConfig | None = None) -> dict:
    """All six workers in one call. Tests and any in-process caller use this."""
    config = config or EngineConfig()
    results = [run_worker(snapshot, as_of, config, worker.KEY) for worker in WORKERS]
    return assemble(snapshot, as_of, config, results)
