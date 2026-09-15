"""Audit every generated archetype with the real engine and report what it found.

This is the honest test of the whole package. Missing data does not produce a low score:
`scoring.py` drops unevaluated checks from the denominator, so a sparse profile reports
low coverage and a `not_evaluated` grade instead. Running the real workers over the
generated snapshot is the only way to know the data is bad in the way the engine
measures rather than merely thin.

    uv run python -m generator_data --verify
    uv run python -m generator_data --verify --rules riverside-grill
"""

from __future__ import annotations

from datetime import date

from app.services.recommendations.engine import analyze
from generator_data.archetypes import ARCHETYPES, Archetype
from generator_data.generator import generate
from generator_data.snapshot import snapshot_of

CATEGORY_ORDER = ("profile", "reputation", "visibility", "operations", "performance", "content")


def audit(archetype: Archetype, reference: date | None = None) -> dict:
    """Generate the archetype and run all six workers over it."""
    reference = reference or date.today()
    return analyze(snapshot_of(generate(archetype, reference)), reference)


def summary(archetype: Archetype, report: dict) -> dict:
    health = report["location"]["health"]
    by_category = {c["category"]: c["score"] for c in health["categories"]}
    states: dict[str, str] = {e["rule"]: e["state"] for e in report["evaluations"]}
    return {
        "key": archetype.key,
        "industry": archetype.industry,
        "score": health["score"],
        "grade": health["grade"],
        "coverage": health["coverage"],
        "issues": health["issues"],
        "categories": by_category,
        "triggered": sorted(r for r, s in states.items() if s == "triggered"),
        "abstained": sorted(r for r, s in states.items() if s == "insufficient_data"),
        "failing_scores": {c: by_category.get(c) for c in archetype.failing},
    }


def run(reference: date | None = None) -> list[dict]:
    return [summary(a, audit(a, reference)) for a in ARCHETYPES]


def main(rules_for: str | None = None, reference: date | None = None) -> int:
    results = run(reference)
    header = f"{'key':<26}{'industry':<14}{'score':>6}{'grade':>7}{'cov':>6}{'items':>6}  "
    header += "".join(f"{c[:4]:>6}" for c in CATEGORY_ORDER)
    print(header)
    print("-" * len(header))
    for row in results:
        line = (
            f"{row['key']:<26}{row['industry']:<14}{row['score']!s:>6}{row['grade']:>7}"
            f"{row['coverage']:>6.2f}{row['issues']:>6}  "
        )
        line += "".join(f"{row['categories'][c]!s:>6}" for c in CATEGORY_ORDER)
        print(line)

    graded = [r["score"] for r in results if r["score"] is not None]
    print(f"\n{len(graded)} of {len(results)} scored; range {min(graded)}-{max(graded)}")
    for name in ("poor", "fair", "good", "excellent", "not_evaluated"):
        count = sum(1 for r in results if r["grade"] == name)
        if count:
            print(f"  {name:<14} {count}")

    if rules_for:
        row = next(r for r in results if r["key"] == rules_for)
        print(f"\n{rules_for}: {len(row['triggered'])} checks triggered")
        for rule in row["triggered"]:
            print(f"  triggered   {rule}")
        for rule in row["abstained"]:
            print(f"  abstained   {rule}")
    return 0
