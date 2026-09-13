from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ENGINE_VERSION = "3.0.0"

Severity = Literal["critical", "warning", "notice"]
State = Literal["triggered", "clear", "insufficient_data", "suppressed"]


class EngineConfig(BaseModel):
    """Tunable thresholds, declared by the worker that reads them.

    Each worker adds its own fields here as it is built, so a threshold is never buried
    in a rule body. `extra="forbid"` rejects a knob no worker reads. Every value is an
    operating policy, not a Google rule, unless the comment says otherwise.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Profile worker
    description_min_chars: int = Field(250, ge=50, le=750)
    description_max_chars: int = Field(750, ge=100, le=750)  # Google's hard cap
    description_max_term_repeats: int = Field(4, ge=2, le=20)
    min_additional_categories: int = Field(2, ge=0, le=9)  # Google allows up to 9
    attribute_coverage_min: float = Field(0.5, gt=0, le=1)


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # An audit is about one business profile.
    location_id: UUID
    as_of: date | None = None
    config: EngineConfig = Field(default_factory=EngineConfig)


class Evidence(BaseModel):
    source: str
    row_ids: list[str]
    fields: list[str]
    calculation: str
    values: dict


class Suggestion(BaseModel):
    """A generated draft for a field the audit found missing or weak.

    Never a fact: the deterministic verdict stands on its own, and a person reviews the
    suggestion before anything is published. Facts only the business knows (phone,
    address, hours, website) are never drafted.
    """

    field: str
    value: str | list[str] | dict
    reason: str
    confidence: Literal["high", "medium", "low"]
    source: str
    model: str
    generated_at: str


class Recommendation(BaseModel):
    key: str
    rule: str
    subject: str = ""
    location_id: str
    location_name: str
    category: str
    category_label: str
    title: str
    action: str
    why: str
    score: int
    severity: Severity
    confidence: Literal["high", "medium"]
    confidence_reason: str
    limitation: str
    evidence: list[Evidence]
    href: str
    explanation_source: str = "deterministic"
    suggestion: Suggestion | None = None


class Evaluation(BaseModel):
    location_id: str
    rule: str
    category: str
    state: State
    reason: str
    issues: int = 0
    evaluated: int = 1


class CategoryScore(BaseModel):
    category: str
    label: str
    weight: int
    score: int | None
    checks_passed: int
    checks_failed: int
    checks_not_evaluated: int
    issues: int
    worst_severity: Severity | None


class HealthScore(BaseModel):
    score: int | None
    grade: Literal["excellent", "good", "fair", "poor", "not_evaluated"]
    coverage: float
    checks_passed: int
    checks_failed: int
    checks_not_evaluated: int
    issues: int
    categories: list[CategoryScore]
    basis: str
