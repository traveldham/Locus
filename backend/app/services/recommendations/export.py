"""Generate from existing data; never seed or overwrite operational records.

uv run python -m app.services.recommendations.export --organization <slug> \
    --as-of 2026-09-11 --output ../locus-intelligence-assignment/output
"""

import argparse
import asyncio
import json
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models import Location, Organization
from app.services.recommendations.runs import generate
from app.services.recommendations.scoring import SEVERITY_ORDER, summarize


def merge(runs: list) -> dict:
    """One deliverable from many single-profile audits, rolled up for reading."""
    first = runs[0].report
    locations = [loc for run in runs for loc in run.report["locations"]]
    items = [item for run in runs for item in run.report["items"]]
    evaluations = [e for run in runs for e in run.report["evaluations"]]
    items.sort(key=lambda r: (-r["score"], r["location_name"], r["key"]))
    locations.sort(
        key=lambda loc: (loc["health"]["score"] is None, loc["health"]["score"] or 0, loc["name"])
    )
    counts: dict[str, int] = {}
    for run in runs:
        for key, value in run.report["counts"].items():
            counts[key] = counts.get(key, 0) + value
    return {
        **first,
        "health": summarize(locations, items, evaluations),
        "locations": locations,
        "items": items,
        "evaluations": evaluations,
        "counts": counts,
        "changes": [change for run in runs for change in run.report["changes"]],
        "fingerprints": {str(run.location_id): run.report["fingerprint"] for run in runs},
    }


def bar(score, width: int = 20) -> str:
    if score is None:
        return "not evaluated"
    filled = round(width * score / 100)
    return f"`{'#' * filled}{'.' * (width - filled)}` {score}/100"


def markdown(report: dict) -> str:
    health = report["health"]
    lines = [
        "# Location audit",
        "",
        f"Analysis date: {report['as_of']}",
        f"Engine: {report['engine_version']}",
        f"Profiles audited: {len(report.get('fingerprints', {}))}",
        "",
        f"## Fleet health {bar(health['score'])} ({health['grade']})",
        "",
        f"{health['locations_scored']} of {health['locations_total']} locations scored. "
        f"{len(report['items'])} open issues: "
        + ", ".join(
            f"{health['severity'][name]} {name}"
            for name in SEVERITY_ORDER
            if health["severity"].get(name)
        )
        + ".",
        "",
        health["basis"],
        "",
        "### Issues by category",
        "",
        "| Category | Weight | Avg score | Issues | Locations | Worst |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in health["by_category"]:
        lines.append(
            f"| {row['label']} | {row['weight']} | "
            f"{row['average_score'] if row['average_score'] is not None else 'n/a'} | "
            f"{row['issues']} | {row['locations_affected']} | {row['worst_severity'] or '-'} |"
        )
    lines += ["", "### Lowest scoring locations", ""]
    lines += [f"- {row['name']}: {row['score']}/100" for row in health["worst_locations"]] or [
        "- No location has a score."
    ]
    lines.append("")

    for location in report["locations"]:
        score = location["health"]
        lines += [
            f"## {location.get('source_location_id') or location['id']} - {location['name']}",
            "",
            f"Health {bar(score['score'])} ({score['grade']}). "
            f"{score['checks_passed']} checks passed, {score['checks_failed']} failed, "
            f"{score['checks_not_evaluated']} not evaluated "
            f"({score['coverage']:.0%} coverage).",
            "",
            "| Category | Score | Passed | Failed | Not evaluated | Issues |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for row in score["categories"]:
            lines.append(
                f"| {row['label']} | {row['score'] if row['score'] is not None else 'n/a'} | "
                f"{row['checks_passed']} | {row['checks_failed']} | "
                f"{row['checks_not_evaluated']} | {row['issues']} |"
            )
        available = [m for m in location["metrics"] if m["available"]]
        if available:
            lines += ["", "Metrics:", ""]
            for m in available:
                suffix = {"percent": "%", "rating": " stars", "days": " days", "rank": ""}.get(
                    m["unit"], ""
                )
                delta = (
                    f" ({m['change_pct']:+.1%} vs previous window)"
                    if m["change_pct"] is not None
                    else ""
                )
                lines.append(f"- {m['label']}: {m['value']:g}{suffix}{delta}")
        items = [r for r in report["items"] if r["location_id"] == location["id"]]
        lines.append("")
        if not items:
            lines += ["No issues found; see coverage for checks that could not be evaluated.", ""]
        for item in items:
            lines += [
                f"### [{item['severity']}] {item['title']}",
                "",
                f"{item['category_label']} - score {item['score']}/100. "
                f"Evidence confidence: {item['confidence']}.",
                "",
                item["why"],
                "",
                item["action"],
                "",
                f"Limit: {item['limitation']}",
                "",
            ]
            for e in item["evidence"]:
                lines += [
                    f"- {e['source']}: {e['calculation']}. "
                    f"Values: `{json.dumps(e['values'], ensure_ascii=False)}`. "
                    f"{len(e['row_ids'])} source records (IDs and full rows in JSON)."
                ]
            lines.append("")
        lines += ["Coverage:", ""]
        lines += [
            f"- {e['rule']}: {e['state']} - {e['reason']}"
            for e in report["evaluations"]
            if e["location_id"] == location["id"]
        ]
        lines.append("")
    return "\n".join(lines)


async def main(args):
    if args.as_of > datetime.now(UTC).date():
        raise SystemExit("Analysis date must not be in the future")
    try:
        async with SessionLocal() as db:
            org = await db.scalar(
                select(Organization).where(Organization.slug == args.organization)
            )
            if org is None:
                raise SystemExit("Organization not found; seed/import data before generating.")
            locations = (
                await db.scalars(
                    select(Location)
                    .where(Location.organization_id == org.id)
                    .order_by(Location.title)
                )
            ).all()
            if not locations:
                raise SystemExit("This organization has no locations to audit.")

            # Each profile is audited on its own, then the reports are merged into one
            # deliverable. The merge is presentation only; nothing is recomputed.
            runs = []
            for location in locations:
                runs.append(await generate(db, org.id, location.id, args.as_of))
                print(f"  audited {location.title}")

            report = merge(runs)
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "recommendations.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            # Only cited evidence is exported; each profile's full snapshot stays in its run.
            cited: dict[str, set[str]] = {}
            for item in report["items"]:
                for evidence in item["evidence"]:
                    cited.setdefault(evidence["source"], set()).update(evidence["row_ids"])
            records: dict[str, list] = {}
            for run in runs:
                for source, ids in cited.items():
                    rows = [r for r in run.snapshot.get(source, []) if r["id"] in ids]
                    records.setdefault(source, []).extend(rows)
            for source in records:
                records[source].sort(key=lambda row: row["id"])
            (args.output / "evidence.json").write_text(
                json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            (args.output / "recommendations.md").write_text(markdown(report), encoding="utf-8")
            print(
                f"Saved {len(report['items'])} actions for {len(report['locations'])} locations "
                f"to {args.output}."
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization", required=True, help="Organization slug")
    parser.add_argument("--as-of", required=True, type=date.fromisoformat)
    parser.add_argument("--output", required=True, type=Path)
    asyncio.run(main(parser.parse_args()))
