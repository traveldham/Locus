from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

__all__ = ["Base", "DataSource", "TimestampMixin", "utcnow"]


def utcnow() -> datetime:
    return datetime.now(UTC)


class DataSource(StrEnum):
    """Where a row's data originates, permanently.

    This is not the "is it sample data yet?" question — that one disappears the day
    Google approves the app. This one never changes: four of our datasets (competitors,
    keyword ranks, tracked keywords, bookings) have no Google API behind them and never
    will, so they are written as `locus` from the moment they are created and the API
    reports that. The UI renders whatever the row says rather than hardcoding a list of
    tables, so the mark cannot drift away from the data.
    """

    google = "google"
    locus = "locus"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
