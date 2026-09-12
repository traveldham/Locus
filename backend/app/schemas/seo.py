from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import DataSource, SearchIntent


class KeywordRankPoint(BaseModel):
    """One week on a rank chart. `rank_absolute` is None when the location was not
    found — a gap in the line, never a plotted zero."""

    model_config = ConfigDict(from_attributes=True)

    week_start: date
    rank_absolute: int | None = None
    rank_in_local_pack: int | None = None
    found: bool = False
    result_url: str | None = None


class TrackedKeywordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    external_keyword_id: str
    keyword: str
    search_intent: SearchIntent | None = None
    device: str | None = None
    tracking_started_on: date | None = None
    # The most recent week's `rank_absolute`. None when that week's check did not find
    # the location — a gap, never a zero and never "unranked = last".
    latest_rank: int | None = None
    source: DataSource = DataSource.locus


class KeywordRankSeriesResponse(BaseModel):
    keyword: TrackedKeywordResponse
    points: list[KeywordRankPoint] = []
    # Weeks the location made the three-result local pack, out of weeks checked.
    weeks_in_local_pack: int = 0
    weeks_checked: int = 0
    source: DataSource = DataSource.locus


class TrackedKeywordListResponse(BaseModel):
    items: list[TrackedKeywordResponse]
    total: int
    source: DataSource = DataSource.locus


class CompetitorObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tracked_keyword_id: UUID
    week_start: date
    competitor_name: str
    competitor_place_id: str | None = None
    rank_absolute: int | None = None
    review_count: int | None = None
    average_rating: float | None = None
    photo_count: int | None = None
    is_claimed: bool | None = None
    source: DataSource = DataSource.locus


class CompetitorListResponse(BaseModel):
    items: list[CompetitorObservationResponse]
    total: int
    # The week actually shown — echoed back because the caller may have left it to us to
    # pick the most recent one.
    week_start: date | None = None
    source: DataSource = DataSource.locus
