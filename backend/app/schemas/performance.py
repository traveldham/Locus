from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import BookingChannel, BookingStatus, DataSource


class PerformancePoint(BaseModel):
    """One day on a performance chart.

    Every metric stays optional: a missing day is plotted as a gap, never as a zero.
    """

    model_config = ConfigDict(from_attributes=True)

    date: date
    impressions_maps_desktop: int | None = None
    impressions_maps_mobile: int | None = None
    impressions_search_desktop: int | None = None
    impressions_search_mobile: int | None = None
    website_clicks: int | None = None
    call_clicks: int | None = None
    direction_requests: int | None = None
    conversations: int | None = None
    bookings: int | None = None


class PerformanceTotals(BaseModel):
    """Period totals. `days_with_data` is what makes them honest — a total over 40 of
    90 days is a different number from a total over all 90, and the caller can say so."""

    impressions_total: int = 0
    impressions_maps: int = 0
    impressions_search: int = 0
    impressions_desktop: int = 0
    impressions_mobile: int = 0
    website_clicks: int = 0
    call_clicks: int = 0
    direction_requests: int = 0
    conversations: int = 0
    bookings: int = 0
    days_with_data: int = 0


class PerformanceSeriesResponse(BaseModel):
    location_id: UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    points: list[PerformancePoint] = []
    totals: PerformanceTotals = PerformanceTotals()
    source: DataSource = DataSource.google


class SearchTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    year_month: str
    search_term: str
    impressions: int | None = None
    # True when `impressions` is Google's "fewer than N" ceiling rather than a count.
    # The UI must render it as "<N", not as N.
    is_threshold: bool = False
    source: DataSource = DataSource.google


class SearchTermListResponse(BaseModel):
    items: list[SearchTermResponse]
    total: int
    limit: int = 0
    offset: int = 0
    source: DataSource = DataSource.google


class BookingResponse(BaseModel):
    """Lives here beside performance because the aggregate `bookings` metric and these
    individual records are read together — and have different provenance, which is
    exactly what the `source` field on each makes visible."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_id: UUID
    location_title: str | None = None
    external_booking_id: str
    customer_name: str | None = None
    service: str | None = None
    requested_for_date: date | None = None
    status: BookingStatus
    booking_source: BookingChannel | None = None
    booking_created_at: datetime | None = None
    # What the client means by "created": when the booking system took the request. The
    # router sets it from `Booking.booking_created_at` *after* validation, because
    # `from_attributes` would otherwise fill it from `TimestampMixin.created_at` — our
    # row-write time, which is a different fact and never the one a booking list wants.
    created_at: datetime | None = None
    source: DataSource = DataSource.locus


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    limit: int = 0
    offset: int = 0
    # Counts per status, for the summary strip above the list.
    status_counts: dict[str, int] = {}
    source: DataSource = DataSource.locus


class SampleDataLoadResponse(BaseModel):
    """What one run of the sample dataset loader wrote, per table."""

    locations_matched: int = 0
    total: int = 0
    counts: dict[str, int] = {}
