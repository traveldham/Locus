from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, DataSource, TimestampMixin


class BookingStatus(StrEnum):
    new = "new"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class BookingChannel(StrEnum):
    website = "website"
    google_profile = "google_profile"
    phone = "phone"
    walk_in = "walk_in"


class Booking(TimestampMixin, Base):
    """One appointment request, from the customer's booking system or CRM.

    Never from Google. Google's performance API reports a *bookings count* attributed to
    the profile and nothing else — no customer, no service, no status, no cancellation.
    Individual records like these can only come from the system that actually took the
    appointment, which is why every row is `source = locus`. The aggregate Google number
    lives separately on `performance_daily.bookings`; the two will not agree, and the
    provenance mark is what makes that legible instead of alarming.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("location_id", "external_booking_id"),
        # The screen is "one location, upcoming or recent first".
        Index("ix_bookings_location_id_requested_for_date", "location_id", "requested_for_date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))

    external_booking_id: Mapped[str] = mapped_column(String(64))
    customer_name: Mapped[str | None] = mapped_column(String(320), nullable=True)
    service: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_for_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus, name="booking_status"))
    # The channel the request arrived through. Named `booking_source` so it cannot be
    # confused with `source`, which answers a different question entirely: this one says
    # how the customer reached us, that one says where the row itself came from.
    booking_source: Mapped[BookingChannel | None] = mapped_column(
        Enum(BookingChannel, name="booking_channel"), nullable=True
    )
    # When the request was made, as recorded by the booking system. Distinct from the
    # inherited `created_at`, which is when we wrote the row.
    booking_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.locus
    )
