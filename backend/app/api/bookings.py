"""Individual appointment requests, from the customer's booking system or CRM.

Never from Google. Google's performance API reports a *bookings count* attributed to the
profile and nothing else — no customer, no service, no status — so every row here is
`source = locus` and the aggregate on `performance_daily.bookings` is a separate number
that will not reconcile with it. Making that legible is the point of the mark.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import DbSession
from app.api.scoping import OrganizationId
from app.models import Booking, BookingChannel, BookingStatus, DataSource, Location
from app.schemas import BookingListResponse, BookingResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


async def owned_location(db: DbSession, organization_id: UUID, location_id: UUID) -> None:
    owns = await db.scalar(
        select(Location.id).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if owns is None:
        raise HTTPException(status_code=404, detail="Location not found")


def serialize(booking: Booking, location_title: str | None) -> BookingResponse:
    item = BookingResponse.model_validate(booking)
    item.location_title = location_title
    # Overwrites what `from_attributes` picked up from `TimestampMixin.created_at`, which
    # is when *we* wrote the row. The client means when the request was made.
    item.created_at = booking.booking_created_at
    return item


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    organization_id: OrganizationId,
    db: DbSession,
    location_id: UUID | None = None,
    status: BookingStatus | None = None,
    booking_source: BookingChannel | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> BookingListResponse:
    """Appointment requests, soonest-requested date first."""
    conditions = [Booking.organization_id == organization_id]

    if location_id is not None:
        await owned_location(db, organization_id, location_id)
        conditions.append(Booking.location_id == location_id)
    if booking_source is not None:
        conditions.append(Booking.booking_source == booking_source)

    # The summary strip counts every status under the other filters, so selecting one
    # status does not empty the strip that is meant to let you switch between them.
    counts = await db.execute(
        select(Booking.status, func.count()).where(*conditions).group_by(Booking.status)
    )
    status_counts = {str(value): count for value, count in counts.all()}

    if status is not None:
        conditions.append(Booking.status == status)

    total = (await db.scalar(select(func.count()).select_from(Booking).where(*conditions))) or 0
    result = await db.execute(
        select(Booking, Location.title)
        .join(Location, Location.id == Booking.location_id)
        .where(*conditions)
        # Newest requested date first; the id keeps paging stable across ties and past
        # rows whose requested date was never filled in.
        .order_by(Booking.requested_for_date.desc().nulls_last(), Booking.id)
        .limit(limit)
        .offset(offset)
    )
    return BookingListResponse(
        items=[serialize(booking, title) for booking, title in result.all()],
        total=total,
        limit=limit,
        offset=offset,
        status_counts=status_counts,
        source=DataSource.locus,
    )
