from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ENGINE_VERSION = "4.0.0"

Severity = Literal["critical", "warning", "notice"]
State = Literal["triggered", "clear", "insufficient_data", "suppressed"]


class EngineConfig(BaseModel):
    """Tunable thresholds, declared by the worker that reads them.

    Each worker adds its own fields here as it is built, so a threshold is never buried
    in a rule body. `extra="forbid"` rejects a knob no worker reads. Every value is an
    operating policy, not a Google rule, unless the comment says otherwise.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # ---- profile worker ----
    description_min_chars: int = Field(250, ge=50, le=750)
    description_max_chars: int = Field(750, ge=100, le=750)  # Google's hard cap
    description_max_term_repeats: int = Field(4, ge=2, le=20)
    min_additional_categories: int = Field(2, ge=0, le=9)  # Google allows up to 9
    attribute_coverage_min: float = Field(0.5, gt=0, le=1)

    # ---- reputation worker ----
    rating_window_days: int = Field(90, ge=30, le=365)
    rating_warning_min: float = Field(4.0, ge=1, le=5)
    rating_critical_min: float = Field(3.5, ge=1, le=5)
    min_reviews: int = Field(5, ge=1, le=100)
    one_star_share_max: float = Field(0.10, gt=0, le=1)
    rating_drop_max: float = Field(0.3, gt=0, le=4)
    competitor_review_ratio_min: float = Field(0.5, gt=0, le=1)
    review_gap_max_days: int = Field(30, ge=1, le=365)
    reviews_per_month_min: int = Field(3, ge=1, le=100)
    reply_rate_min: float = Field(0.6, gt=0, le=1)
    critical_reply_rate_min: float = Field(0.8, gt=0, le=1)
    min_critical_reviews: int = Field(3, ge=1, le=100)
    reply_wait_days: int = Field(3, ge=0, le=60)
    reply_delay_max_days: int = Field(7, ge=1, le=90)
    unanswered_list_max: int = Field(10, ge=1, le=50)
    review_lookback_days: int = Field(365, ge=30, le=1095)

    # ---- visibility worker ----
    # Rank checks are weekly; a latest check older than this abstains every rank rule.
    rank_freshness_days: int = Field(21, ge=7, le=90)
    rank_trend_weeks: int = Field(4, ge=2, le=13)
    pack_share_min: float = Field(0.25, gt=0, le=1)
    near_pack_low: int = Field(4, ge=2, le=10)
    near_pack_high: int = Field(8, ge=4, le=20)
    near_pack_min_weeks: int = Field(2, ge=1, le=13)
    not_found_min_weeks: int = Field(4, ge=2, le=13)  # consecutive, ending in the latest
    rank_drop_min_positions: int = Field(3, ge=1, le=20)  # latest vs mean of prior weeks
    high_intent_intents: tuple[str, ...] = ("emergency", "implants", "orthodontics")
    high_intent_lag_positions: int = Field(3, ge=1, le=20)  # behind the other keywords
    term_loss_min_impressions: int = Field(200, ge=1)  # in the earlier month
    term_loss_share: float = Field(0.5, gt=0, le=1)
    rival_review_ratio: float = Field(1.5, ge=1)
    rival_rating_gap: float = Field(0.3, ge=0, le=4)
    rival_photo_ratio: float = Field(1.5, ge=1)
    rival_min_keywords_ahead: int = Field(3, ge=1)

    # ---- operations worker ----
    booking_window_days: int = Field(90, ge=14, le=365)  # requests judged by creation date
    booking_wait_days: int = Field(3, ge=1, le=30)  # a "new" request older than this is stale
    booking_min_requests: int = Field(10, ge=1, le=500)  # denominator floor for rate checks
    booking_min_settled: int = Field(10, ge=1, le=500)  # completed + cancelled + no-show floor
    booking_confirmation_min: float = Field(0.7, gt=0, le=1)
    booking_cancellation_max: float = Field(0.2, gt=0, le=1)
    booking_no_show_max: float = Field(0.1, gt=0, le=1)
    booking_weekend_min_requests: int = Field(5, ge=1, le=500)
    booking_lead_recent_days: int = Field(28, ge=7, le=180)  # recent slice for lead-time trend
    booking_lead_collapse_ratio: float = Field(0.5, gt=0, lt=1)
    booking_channel_share_max: float = Field(0.9, gt=0.5, le=1)

    # ---- performance worker ----
    # Windows are a multiple of 7 so both hold the same weekday mix; days are paired
    # with the same weekday one window earlier.
    performance_window_days: int = Field(28, ge=7, le=91, multiple_of=7)
    # Data older than this before as-of is stale: every trend check abstains.
    performance_max_stale_days: int = Field(14, ge=1, le=90)
    # Share of window days that must pair (both windows report the metric).
    performance_min_paired_share: float = Field(0.7, gt=0, le=1)
    # Volume floors before any percentage is computed.
    performance_min_impressions: int = Field(200, ge=1)
    performance_min_actions: int = Field(30, ge=1)
    # Relative declines that start a finding (notice), graded up from there.
    performance_impressions_decline: float = Field(0.10, gt=0, lt=1)
    performance_actions_decline: float = Field(0.15, gt=0, lt=1)
    performance_action_rate_decline: float = Field(0.15, gt=0, lt=1)
    # Absolute shift in Maps share or mobile share of impressions, in fraction points.
    performance_split_shift_points: float = Field(0.10, gt=0, lt=1)
    # Days in a row with impressions but every action reported as zero.
    performance_zero_action_streak_days: int = Field(3, ge=2, le=28)
    performance_zero_action_min_impressions: int = Field(20, ge=1)
    # Calendar days missing from the current window before it is noticed.
    performance_data_gap_days: int = Field(3, ge=1, le=28)

    # ---- content worker ----
    content_photo_floor: int = Field(10, ge=1, le=200)  # fewer photos than this is a warning
    content_photo_target: int = Field(30, ge=1, le=500)  # a working target, above the floor
    content_photo_stale_days: int = Field(90, ge=7, le=730)
    content_post_gap_days: int = Field(30, ge=7, le=365)  # days without a post before it fires
    content_post_window_days: int = Field(180, ge=30, le=365)  # Google archives posts at 6 months
    content_posts_min_90d: int = Field(6, ge=1, le=90)  # roughly one every two weeks
    content_post_mix_min_posts: int = Field(3, ge=2, le=50)  # posts needed to judge mix and CTAs
    content_post_cta_max_missing_share: float = Field(0.5, ge=0, le=1)


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
