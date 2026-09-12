from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import DataSource, PostCtaType, PostType


class MediaSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    location_id: UUID
    # Filled by the router: the media screen lists every location at once, so each
    # rollup has to name the profile it belongs to.
    location_title: str | None = None
    photo_count: int | None = None
    interior_photo_count: int | None = None
    exterior_photo_count: int | None = None
    team_photo_count: int | None = None
    video_count: int | None = None
    has_profile_photo: bool = False
    has_cover_photo: bool = False
    last_photo_uploaded_on: date | None = None
    source: DataSource = DataSource.google


class MediaSummaryListResponse(BaseModel):
    items: list[MediaSummaryResponse]
    total: int = 0
    source: DataSource = DataSource.google


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    location_title: str | None = None
    google_post_id: str
    post_type: PostType
    summary: str | None = None
    cta_type: PostCtaType | None = None
    published_on: date | None = None
    source: DataSource = DataSource.google


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
    limit: int = 0
    offset: int = 0
    source: DataSource = DataSource.google
