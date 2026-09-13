"""Versioned audit policy: category weights, severity bands and penalties.

Every number here is an explicit operating decision, not a measured business fact.
Changing one changes the health score, so it belongs in the engine version. The checks
themselves live with their worker under `categories/`; this module only gathers them.
"""

from app.services.recommendations.categories import WORKERS
from app.services.recommendations.types import Severity

# One entry per worker, in audit order. Weights sum to 100.
CATEGORIES: dict[str, dict] = {
    worker.KEY: {
        "label": worker.LABEL,
        "weight": worker.WEIGHT,
        "rules": {rule: spec["weight"] for rule, spec in worker.CHECKS.items()},
    }
    for worker in WORKERS
}
assert sum(spec["weight"] for spec in CATEGORIES.values()) == 100

RULE_CATEGORY = {rule: name for name, spec in CATEGORIES.items() for rule in spec["rules"]}

# What each check looks at and what to do about it, declared by the worker that owns it.
RULE_DOCS: dict[str, dict] = {
    rule: {key: value for key, value in spec.items() if key != "weight"}
    for worker in WORKERS
    for rule, spec in worker.CHECKS.items()
}

# Score bands. A score orders work; it is not a probability or a predicted gain.
CRITICAL_SCORE = 75
WARNING_SCORE = 45

# How much of a rule's category credit a triggered finding removes, by worst severity.
SEVERITY_PENALTY: dict[str, float] = {"critical": 1.0, "warning": 0.6, "notice": 0.25}

# A rule that enumerates every affected subject is scored on the share of the subjects
# it checked that failed, never on the raw count. A single failure still costs this
# floor share of the severity penalty.
ENUMERATED_FLOOR = 0.4

GRADES = (("excellent", 90), ("good", 75), ("fair", 50), ("poor", 0))


def severity_of(score: int) -> Severity:
    if score >= CRITICAL_SCORE:
        return "critical"
    return "warning" if score >= WARNING_SCORE else "notice"


def grade_of(score: int | None) -> str:
    if score is None:
        return "not_evaluated"
    return next(name for name, floor in GRADES if score >= floor)


def graded(base: int, magnitude: float, span: int, cap: int) -> int:
    """Scale a rule's floor score by how far past its threshold the finding sits.

    `magnitude` is a 0..1 fraction of the way from the trigger point to the point
    the policy treats as fully severe. Bands are policy, not calibrated risk.
    """
    return int(min(cap, base + round(span * max(0.0, min(1.0, magnitude)))))
