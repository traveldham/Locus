from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ENGINE_VERSION = "2.0.0"

Severity = Literal["critical", "warning", "notice"]
State = Literal["triggered", "clear", "insufficient_data", "suppressed"]


class EngineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    window_days: int = Field(28, ge=14, le=84, multiple_of=7)
    outcome_window_days: int = Field(90, ge=28, le=365)
    min_daily_coverage: float = Field(0.8, ge=0.5, le=1)
    decline_fraction: float = Field(0.2, gt=0, le=0.8)
    decline_notice_fraction: float = Field(0.1, gt=0, le=0.8)
    min_impressions: int = Field(200, ge=1)
    min_reviews: int = Field(5, ge=3)
    reply_wait_days: int = Field(3, ge=1, le=30)
    booking_wait_days: int = Field(2, ge=1, le=30)
    min_completed_visits: int = Field(20, ge=5)
    failed_visit_fraction: float = Field(0.2, gt=0, le=1)
    post_gap_days: int = Field(45, ge=14, le=180)
    freshness_days: int = Field(14, ge=1, le=90)


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
    change: str = "new"
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


class Metric(BaseModel):
    key: str
    label: str
    category: str
    value: float | None = None
    unit: Literal["count", "percent", "rating", "days", "rank"] = "count"
    previous: float | None = None
    change_pct: float | None = None
    direction: Literal["up_is_good", "down_is_good", "neutral"] = "neutral"
    available: bool = True
    basis: str = ""
