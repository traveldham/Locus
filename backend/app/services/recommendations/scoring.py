"""Health scoring: turn rule verdicts into a comparable score per location.

Unevaluated checks are excluded from the denominator rather than counted as passes.
A location with little data therefore reports low coverage, not a flattering score.
"""

from collections import Counter

from app.services.recommendations.policy import (
    CATEGORIES,
    ENUMERATED_FLOOR,
    RULE_CATEGORY,
    RULE_DOCS,
    SEVERITY_PENALTY,
    grade_of,
)
from app.services.recommendations.types import CategoryScore, HealthScore

SEVERITY_ORDER = ("critical", "warning", "notice")

BASIS = (
    "Weighted share of evaluated checks that passed, reduced by each failing check's "
    "severity and by the share of the subjects it examined that failed. Checks without "
    "enough evidence are excluded from the score, never counted as passes."
)


def worst(severities: list[str]) -> str | None:
    return next((s for s in SEVERITY_ORDER if s in severities), None)


def penalty_for(verdict: dict, rule_items: list[dict]) -> float:
    """Share of a rule's credit removed, from worst severity and how widely it failed.

    The numerator is what the rule itself declared failed, not how many findings it
    wrote: a rule that reports five unanswered reviews as one action still failed five
    of the reviews it checked.
    """
    severity = SEVERITY_PENALTY[worst([r["severity"] for r in rule_items]) or "notice"]
    checked = max(1, verdict.get("evaluated", 1))
    if checked <= 1:
        return severity
    share = min(1.0, max(verdict.get("issues", 0), len(rule_items)) / checked)
    return min(1.0, severity * (ENUMERATED_FLOOR + (1 - ENUMERATED_FLOOR) * share))


def score_location(location_id: str, evaluations: list[dict], items: list[dict]) -> HealthScore:
    mine = [e for e in evaluations if e["location_id"] == location_id]
    findings = [r for r in items if r["location_id"] == location_id]
    categories: list[CategoryScore] = []
    passed = failed = skipped = 0
    for name, spec in CATEGORIES.items():
        earned = possible = 0.0
        c_passed = c_failed = c_skipped = c_issues = 0
        severities: list[str] = []
        for rule, weight in spec["rules"].items():
            verdict = next((e for e in mine if e["rule"] == rule), None)
            if verdict is None or verdict["state"] in ("insufficient_data", "suppressed"):
                c_skipped += 1
                continue
            possible += weight
            if verdict["state"] == "clear":
                earned += weight
                c_passed += 1
                continue
            c_failed += 1
            rule_items = [r for r in findings if r["rule"] == rule]
            severities += [r["severity"] for r in rule_items]
            c_issues += len(rule_items)
            earned += weight * (1 - penalty_for(verdict, rule_items))
        passed, failed, skipped = passed + c_passed, failed + c_failed, skipped + c_skipped
        categories.append(
            CategoryScore(
                category=name,
                label=spec["label"],
                weight=spec["weight"],
                score=round(100 * earned / possible) if possible else None,
                checks_passed=c_passed,
                checks_failed=c_failed,
                checks_not_evaluated=c_skipped,
                issues=c_issues,
                worst_severity=worst(severities),
            )
        )
    scored = [c for c in categories if c.score is not None]
    total_weight = sum(c.weight for c in scored)
    score = round(sum(c.score * c.weight for c in scored) / total_weight) if total_weight else None
    checks = passed + failed + skipped
    return HealthScore(
        score=score,
        grade=grade_of(score),
        coverage=round((passed + failed) / checks, 4) if checks else 0.0,
        checks_passed=passed,
        checks_failed=failed,
        checks_not_evaluated=skipped,
        issues=len(findings),
        categories=categories,
        basis=BASIS,
    )


def check_inventory(items: list[dict], evaluations: list[dict]) -> dict[str, dict]:
    """Every check the engine can run, whether it fired, passed or could not be judged.

    Built the same way for one location and for the whole fleet, so a check that passed
    is never indistinguishable from one that was never evaluated.
    """
    inventory: dict[str, dict] = {}
    for rule, docs in RULE_DOCS.items():
        group = [r for r in items if r["rule"] == rule]
        verdicts = [e for e in evaluations if e["rule"] == rule]
        category = RULE_CATEGORY[rule]
        inventory[rule] = {
            "rule": rule,
            "category": category,
            "category_label": CATEGORIES[category]["label"],
            "label": docs["label"],
            "unit": docs["unit"],
            "predicate": docs["predicate"],
            "predicate_one": docs["predicate_one"],
            "subject": docs["subject"],
            "subject_predicate": docs["subject_predicate"],
            "checks": docs["checks"],
            "fix": docs["fix"],
            "issues": len(group),
            "new_issues": sum(r["change"] == "new" for r in group),
            "locations_affected": len({r["location_id"] for r in group}),
            "locations_passed": sum(e["state"] == "clear" for e in verdicts),
            "locations_not_evaluated": sum(
                e["state"] in ("insufficient_data", "suppressed") for e in verdicts
            ),
            "state": verdicts[0]["state"] if len(verdicts) == 1 else None,
            "reason": verdicts[0]["reason"] if len(verdicts) == 1 else "",
            "subjects_failed": sum(e["issues"] for e in verdicts),
            "subjects_examined": sum(e["evaluated"] for e in verdicts),
            "worst_severity": worst([r["severity"] for r in group]),
            "max_score": max((r["score"] for r in group), default=0),
            "severity": dict(Counter(r["severity"] for r in group)),
        }
    return inventory


def median(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return round((ordered[middle - 1] + ordered[middle]) / 2)


def summarize(locations: list[dict], items: list[dict], evaluations: list[dict]) -> dict:
    """Fleet rollup plus the full check inventory the issues view is built from."""
    scored = [loc["health"]["score"] for loc in locations if loc["health"]["score"] is not None]
    by_category: dict[str, dict] = {}
    for name, spec in CATEGORIES.items():
        group = [r for r in items if r["category"] == name]
        by_category[name] = {
            "category": name,
            "label": spec["label"],
            "weight": spec["weight"],
            "issues": len(group),
            "locations_affected": len({r["location_id"] for r in group}),
            "worst_severity": worst([r["severity"] for r in group]),
            "average_score": (
                round(
                    sum(
                        c["score"]
                        for loc in locations
                        for c in loc["health"]["categories"]
                        if c["category"] == name and c["score"] is not None
                    )
                    / max(
                        1,
                        sum(
                            1
                            for loc in locations
                            for c in loc["health"]["categories"]
                            if c["category"] == name and c["score"] is not None
                        ),
                    )
                )
                if any(
                    c["category"] == name and c["score"] is not None
                    for loc in locations
                    for c in loc["health"]["categories"]
                )
                else None
            ),
        }
    by_rule = check_inventory(items, evaluations)
    fleet = round(sum(scored) / len(scored)) if scored else None
    return {
        "score": fleet,
        "grade": grade_of(fleet),
        "locations_scored": len(scored),
        "locations_total": len(locations),
        "worst_locations": [
            {"id": loc["id"], "name": loc["name"], "score": loc["health"]["score"]}
            for loc in sorted(
                (loc for loc in locations if loc["health"]["score"] is not None),
                key=lambda loc: loc["health"]["score"],
            )[:5]
        ],
        "severity": dict(Counter(r["severity"] for r in items)),
        "by_category": list(by_category.values()),
        "by_rule": list(by_rule.values()),
        "basis": BASIS,
    }
