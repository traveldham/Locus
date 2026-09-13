"""What a worker is handed: one profile's snapshot, the analysis date, and a way to
record verdicts and findings. Workers never touch the database."""

from datetime import date, timedelta
from math import isfinite

from app.services.recommendations.policy import CATEGORIES, RULE_CATEGORY, severity_of
from app.services.recommendations.types import (
    EngineConfig,
    Evaluation,
    Evidence,
    Recommendation,
    State,
)


def day(value) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
        and value >= 0
    )


class Context:
    def __init__(self, snapshot: dict, location: dict, as_of: date, config: EngineConfig):
        self.snapshot, self.location, self.as_of, self.config = snapshot, location, as_of, config
        self.items: list[Recommendation] = []
        self.evaluations: list[Evaluation] = []

    def rows(self, source: str) -> list[dict]:
        return [
            r for r in self.snapshot.get(source, []) if r.get("location_id") == self.location["id"]
        ]

    def window(self, rows: list[dict], field: str, days: int, offset: int = 0) -> list[dict]:
        end = self.as_of - timedelta(days=offset)
        start = end - timedelta(days=days - 1)
        return [r for r in rows if day(r.get(field)) and start <= day(r[field]) <= end]

    def assess(self, rule: str, state: State, reason: str, issues: int = 0, evaluated: int = 1):
        """Exactly one coverage verdict per rule, including when it fires."""
        self.evaluations.append(
            Evaluation(
                location_id=self.location["id"],
                rule=rule,
                category=RULE_CATEGORY[rule],
                state=state,
                reason=reason,
                issues=issues,
                evaluated=evaluated,
            )
        )

    def evidence(
        self, source: str, rows: list[dict], fields: list[str], calculation: str, **values
    ) -> Evidence:
        return Evidence(
            source=source,
            row_ids=sorted(str(r["id"]) for r in rows),
            fields=fields,
            calculation=calculation,
            values=values,
        )

    def emit(
        self,
        rule: str,
        title: str,
        action: str,
        why: str,
        score: int,
        evidence: list[Evidence],
        href: str,
        limitation: str,
        confidence: str = "medium",
        subject: str = "",
    ):
        """Record one finding. Rules that enumerate every affected keyword, term or
        field pass a `subject` so each finding keeps a stable identity."""
        category = RULE_CATEGORY[rule]
        self.items.append(
            Recommendation(
                key=f"{self.location['id']}:{rule}" + (f":{subject}" if subject else ""),
                rule=rule,
                subject=subject,
                location_id=self.location["id"],
                location_name=self.location["title"],
                category=category,
                category_label=CATEGORIES[category]["label"],
                title=title,
                action=action,
                why=why,
                score=score,
                severity=severity_of(score),
                confidence=confidence,
                confidence_reason=(
                    "Directly observed in stored records; outcome is not predicted."
                    if confidence == "high"
                    else "A descriptive pattern supports investigation, not a causal claim."
                ),
                limitation=limitation,
                evidence=evidence,
                href=href,
            )
        )
