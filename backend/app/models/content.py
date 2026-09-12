from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, DataSource, TimestampMixin


class PostType(StrEnum):
    standard = "standard"
    event = "event"
    offer = "offer"
    alert = "alert"


class PostCtaType(StrEnum):
    book = "book"
    call = "call"
    learn_more = "learn_more"
    sign_up = "sign_up"
    get_offer = "get_offer"


class MediaSummary(TimestampMixin, Base):
    """Photo and video counts for one location's profile.

    This is a **rollup, not the source of truth**. The live Google API returns individual
    media items (`locations.media.list`), each with its own id, category, URL and upload
    time; these counts would be derived from that list, not fetched as counts. Keeping
    that explicit matters because it bounds what this table can answer: it can say "44
    photos, 15 of them interior", but it can never show a photo, attribute one to an
    uploader, or delete one. When media items land they get their own table and this
    becomes a cache of them.
    """

    __tablename__ = "media_summary"
    # One rollup per location — a second row would mean two answers to the same question.
    __table_args__ = (UniqueConstraint("location_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))

    photo_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # The category counts need not sum to photo_count; the remainder is uncategorised.
    interior_photo_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exterior_photo_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_photo_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_profile_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    has_cover_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    last_photo_uploaded_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.google
    )


class Post(TimestampMixin, Base):
    """One Google Business Profile post published by a location."""

    __tablename__ = "posts"
    __table_args__ = (
        # Google's post id is stable, so a re-sync updates the post in place.
        UniqueConstraint("location_id", "google_post_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )

    google_post_id: Mapped[str] = mapped_column(String(255))
    post_type: Mapped[PostType] = mapped_column(Enum(PostType, name="post_type"))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Google allows a post with no call to action, so this stays nullable rather than
    # acquiring a "none" member that would be indistinguishable from an unset value.
    cta_type: Mapped[PostCtaType | None] = mapped_column(
        Enum(PostCtaType, name="post_cta_type"), nullable=True
    )
    published_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.google
    )
