"""Do-these-first: one per check, spread across categories, worst first."""

from app.services.recommendations.engine import priorities


def item(key, rule, category, severity, score, suggestion=None):
    return {
        "key": key,
        "rule": rule,
        "category": category,
        "severity": severity,
        "score": score,
        "suggestion": suggestion,
    }


def test_one_per_rule_and_at_most_two_per_category_first():
    items = [
        item(f"ops:{n}", "requests_unanswered", "operations", "critical", 90) for n in range(5)
    ]
    items += [
        item("ops:x", "no_show_rate_high", "operations", "critical", 88),
        item("ops:y", "cancellation_rate_high", "operations", "critical", 87),
        item("p:web", "website_missing", "profile", "critical", 85),
        item("r:rev", "critical_review_unanswered", "reputation", "warning", 70),
        item("v:pack", "pack_share_low", "visibility", "notice", 30),
    ]
    chosen = priorities(items)
    assert chosen[0] == "ops:0"
    assert set(chosen) == {"ops:0", "ops:x", "p:web", "r:rev", "v:pack"}
    # Five stale requests share one check: only the first survives.
    assert sum(k.startswith("ops:") for k in chosen) == 2


def test_drafts_and_quick_fixes_break_ties():
    items = [
        item("a", "rule_a", "profile", "warning", 60),
        item("b", "rule_b", "profile", "warning", 60, suggestion={"field": "x"}),
    ]
    assert priorities(items)[0] == "b"
