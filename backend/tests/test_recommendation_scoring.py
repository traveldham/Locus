"""Health scoring over synthetic verdicts, independent of any worker's checks."""

from app.services.recommendations import policy, scoring
from app.services.recommendations.policy import CATEGORIES
from app.services.recommendations.scoring import check_inventory, penalty_for, score_location


def item(rule, category, score, key="x"):
    return {
        "rule": rule,
        "category": category,
        "score": score,
        "severity": policy.severity_of(score),
        "key": key,
    }


def verdict(rule, category, state, issues=0, evaluated=1):
    return {
        "location_id": "loc",
        "rule": rule,
        "category": category,
        "state": state,
        "reason": "",
        "issues": issues,
        "evaluated": evaluated,
    }


def with_rules(monkeypatch, rules: dict[str, dict[str, int]]):
    """Pretend the workers declared these checks, without touching the worker modules."""
    categories = {name: {**spec, "rules": rules.get(name, {})} for name, spec in CATEGORIES.items()}
    rule_category = {rule: name for name, spec in categories.items() for rule in spec["rules"]}
    docs = {rule: {"label": rule} for rule in rule_category}
    for module in (policy, scoring):
        monkeypatch.setattr(module, "CATEGORIES", categories)
        monkeypatch.setattr(module, "RULE_CATEGORY", rule_category)
        monkeypatch.setattr(module, "RULE_DOCS", docs)


def test_no_checks_means_no_score_not_a_perfect_score():
    health = score_location([], [])
    assert health.score is None and health.grade == "not_evaluated"
    assert health.coverage == 0.0 and health.issues == 0
    assert [c.category for c in health.categories] == list(CATEGORIES)


def test_unevaluated_checks_leave_the_denominator(monkeypatch):
    with_rules(monkeypatch, {"profile": {"a": 1, "b": 1}, "content": {"c": 1}})
    health = score_location(
        [
            verdict("a", "profile", "clear"),
            verdict("b", "profile", "insufficient_data"),
            verdict("c", "content", "suppressed"),
        ],
        [],
    )
    profile = next(c for c in health.categories if c.category == "profile")
    assert profile.score == 100 and profile.checks_not_evaluated == 1
    assert next(c for c in health.categories if c.category == "content").score is None
    # Only the profile category is scored, so its weight is the whole denominator.
    assert health.score == 100 and health.coverage == round(1 / 3, 4)


def test_severity_and_failed_share_drive_the_penalty(monkeypatch):
    with_rules(monkeypatch, {"profile": {"a": 1}})
    critical = [item("a", "profile", 90)]
    notice = [item("a", "profile", 10)]
    single = verdict("a", "profile", "triggered", issues=1, evaluated=1)
    assert penalty_for(single, critical) == 1.0
    assert penalty_for(single, notice) == 0.25
    narrow = verdict("a", "profile", "triggered", issues=1, evaluated=10)
    wide = verdict("a", "profile", "triggered", issues=10, evaluated=10)
    assert penalty_for(narrow, critical) < penalty_for(wide, critical) == 1.0
    assert score_location([single], critical).score == 0
    assert score_location([narrow], critical).score > score_location([wide], critical).score


def test_weighted_categories_combine_into_one_score(monkeypatch):
    with_rules(monkeypatch, {"profile": {"a": 1}, "visibility": {"b": 1}})
    health = score_location(
        [verdict("a", "profile", "clear"), verdict("b", "visibility", "triggered")],
        [item("b", "visibility", 90)],
    )
    # profile 100 × 20 + visibility 0 × 25, over 45.
    assert health.score == round(100 * 20 / 45)
    assert health.checks_passed == 1 and health.checks_failed == 1 and health.issues == 1


def test_check_inventory_lists_passing_and_unevaluated_checks_not_only_failures(monkeypatch):
    with_rules(monkeypatch, {"profile": {"a": 1, "b": 1, "c": 1}})
    inventory = check_inventory(
        [item("a", "profile", 80)],
        [
            verdict("a", "profile", "triggered", issues=3, evaluated=5),
            verdict("b", "profile", "clear"),
        ],
    )
    by_rule = {row["rule"]: row for row in inventory}
    assert by_rule["a"]["issues"] == 1 and by_rule["a"]["worst_severity"] == "critical"
    assert by_rule["a"]["subjects_failed"] == 3 and by_rule["a"]["subjects_examined"] == 5
    assert by_rule["b"]["state"] == "clear" and by_rule["b"]["issues"] == 0
    assert by_rule["c"]["state"] is None and by_rule["c"]["subjects_examined"] == 0


def test_grades_and_severity_bands():
    assert policy.grade_of(None) == "not_evaluated"
    assert policy.grade_of(90) == "excellent" and policy.grade_of(89) == "good"
    assert policy.grade_of(50) == "fair" and policy.grade_of(49) == "poor"
    assert policy.severity_of(75) == "critical" and policy.severity_of(74) == "warning"
    assert policy.severity_of(44) == "notice"
    assert policy.graded(40, 0.5, 20, 55) == 50 and policy.graded(40, 2, 20, 55) == 55
