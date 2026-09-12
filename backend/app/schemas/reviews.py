from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MAX_REPLY_LENGTH = 4096


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    location_title: str | None = None
    google_review_id: str
    google_review_name: str | None = None
    reviewer_display_name: str | None = None
    is_anonymous: bool = False
    star_rating: int
    comment: str | None = None
    create_time: datetime
    update_time: datetime | None = None
    reply_comment: str | None = None
    reply_update_time: datetime | None = None
    has_reply: bool = False


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    limit: int
    offset: int


class ReviewSyncResponse(BaseModel):
    sync_run_id: UUID
    locations_synced: int
    created: int
    updated: int
    total: int
    # Locations whose reviews could not be fetched, each with the reason — a missing
    # account-qualified resource name must be visible, not an empty inbox.
    skipped: list[dict[str, str]] = []


class ReviewReplyRequest(BaseModel):
    # A reply is published on a live public profile, so it is length-capped here as well
    # as trimmed in the router: an empty or whitespace-only reply is rejected, not sent.
    comment: str = Field(min_length=1, max_length=MAX_REPLY_LENGTH)
