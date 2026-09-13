from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ENGINE_VERSION = "3.0.0"

Severity = Literal["critical", "warning", "notice"]
State = Literal["triggered", "clear", "insufficient_data", "suppressed"]


class EngineConfig(BaseModel):
    """Tunable thresholds. Empty until a worker declares the knobs it needs.

    Each worker adds its own fields here as it is built, so a threshold is never buried
    in a rule body. `extra="forbid"` rejects a knob no worker reads.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


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
