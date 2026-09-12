from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Review(TimestampMixin, Base):
    """One customer review of a location, mirrored from Google.

    The owner reply lives inline rather than in its own table: Google returns
    `reviewReply` nested inside the review and allows at most one per review, so a
    child table would only ever hold zero or one row.
    """

    __tablename__ = "reviews"
    __table_args__ = (
        # Google's review id is unique per location, so re-syncing updates in place.
        UniqueConstraint("location_id", "google_review_id"),
        # The inbox is "one location, newest first" — this index serves it directly and
        # makes a separate index on location_id redundant.
        Index("ix_reviews_location_id_create_time", "location_id", "create_time"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))

    google_review_id: Mapped[str] = mapped_column(String(255))
    # The full v4 resource name: accounts/{a}/locations/{l}/reviews/{r}.
    google_review_name: Mapped[str | None] = mapped_column(String(512), nullable=True)

    reviewer_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewer_photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)

    # Google sends the rating as an enum string ("FIVE"); it is normalised to 1-5 on the
    # way in so the inbox can filter and sort on it.
    star_rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reply_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reply_update_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
