"""Health scoring: turn the six workers' verdicts into one comparable score.

Unevaluated checks are excluded from the denominator rather than counted as passes.
A profile with little data therefore reports low coverage, not a flattering score.
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
    """Share of a rule's credit removed, from worst severity and how widely it failed."""
    severity = SEVERITY_PENALTY[worst([r["severity"] for r in rule_items]) or "notice"]
    checked = max(1, verdict.get("evaluated", 1))
    if checked <= 1:
        return severity
    share = min(1.0, max(verdict.get("issues", 0), len(rule_items)) / checked)
    return min(1.0, severity * (ENUMERATED_FLOOR + (1 - ENUMERATED_FLOOR) * share))


def score_location(evaluations: list[dict], items: list[dict]) -> HealthScore:
    categories: list[CategoryScore] = []
    passed = failed = skipped = 0
    for name, spec in CATEGORIES.items():
        earned = possible = 0.0
        c_passed = c_failed = c_skipped = c_issues = 0
        severities: list[str] = []
        for rule, weight in spec["rules"].items():
            verdict = next((e for e in evaluations if e["rule"] == rule), None)
            if verdict is None or verdict["state"] in ("insufficient_data", "suppressed"):
                c_skipped += 1
                continue
            possible += weight
            if verdict["state"] == "clear":
                earned += weight
                c_passed += 1
                continue
            c_failed += 1
            rule_items = [r for r in items if r["rule"] == rule]
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
        issues=len(items),
        categories=categories,
        basis=BASIS,
    )


def check_inventory(items: list[dict], evaluations: list[dict]) -> list[dict]:
    """Every check the engine can run, whether it fired, passed or could not be judged."""
    inventory = []
    for rule, docs in RULE_DOCS.items():
        group = [r for r in items if r["rule"] == rule]
        verdict = next((e for e in evaluations if e["rule"] == rule), None)
        category = RULE_CATEGORY[rule]
        inventory.append(
            {
                "rule": rule,
                "category": category,
                "category_label": CATEGORIES[category]["label"],
                **docs,
                "issues": len(group),
                "state": verdict["state"] if verdict else None,
                "reason": verdict["reason"] if verdict else "",
                "subjects_failed": verdict["issues"] if verdict else 0,
                "subjects_examined": verdict["evaluated"] if verdict else 0,
                "worst_severity": worst([r["severity"] for r in group]),
                "max_score": max((r["score"] for r in group), default=0),
                "severity": dict(Counter(r["severity"] for r in group)),
            }
        )
    return inventory
