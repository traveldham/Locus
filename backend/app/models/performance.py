from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, DataSource, TimestampMixin


class PerformanceDaily(TimestampMixin, Base):
    """One day of Google Business Profile performance for one location.

    Every metric is nullable on purpose. Google's performance API omits a metric for a
    day it has no data for, and an omitted metric is not a zero — "nobody called" and
    "Google did not report calls" are different facts, and defaulting to 0 would quietly
    turn the second into the first in every chart and total.
    """

    __tablename__ = "performance_daily"
    __table_args__ = (
        # Re-syncing a day updates it in place rather than stacking duplicates. The index
        # behind this constraint is also what serves "one location over a date range",
        # which is the only way this table is ever read.
        UniqueConstraint("location_id", "date"),
        # Org-wide rollups across every location for a period.
        Index("ix_performance_daily_organization_id_date", "organization_id", "date"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    location_id: Mapped[UUID] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))

    date: Mapped[date] = mapped_column(Date)

    impressions_maps_desktop: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impressions_maps_mobile: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impressions_search_desktop: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impressions_search_mobile: Mapped[int | None] = mapped_column(Integer, nullable=True)
    website_clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    call_clicks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direction_requests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bookings: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.google
    )


class SearchTermMonthly(TimestampMixin, Base):
    """One search term that surfaced a location, aggregated for one month.

    Google returns each term's volume as *either* an exact `value` or a `threshold`
    ("fewer than 15"), never both — it withholds the exact number for low-volume terms.
    `is_threshold` keeps that distinction, so a term reported as "under 15" is never
    charted, summed or ranked as if it were exactly 15.
    """

    __tablename__ = "search_terms_monthly"
    __table_args__ = (
        UniqueConstraint("location_id", "year_month", "search_term"),
        # The screen is "one location, one month, ordered by impressions".
        Index("ix_search_terms_monthly_location_id_year_month", "location_id", "year_month"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )
    location_id: Mapped[UUID] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"))

    # "2026-04". Stored as text, not a date: the month is the whole grain here, and a
    # date would invite a misleading day component.
    year_month: Mapped[str] = mapped_column(String(7))
    search_term: Mapped[str] = mapped_column(String(512))
    impressions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # True when `impressions` is Google's threshold ceiling rather than a measured count.
    is_threshold: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.google
    )
