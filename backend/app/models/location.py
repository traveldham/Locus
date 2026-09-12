from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class LocationSource(StrEnum):
    google = "google"
    fixture = "fixture"
    manual = "manual"


class OpenStatus(StrEnum):
    open = "open"
    closed_temporarily = "closed_temporarily"
    closed_permanently = "closed_permanently"


class Location(TimestampMixin, Base):
    """A Google Business Profile location mirrored into our database."""

    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("organization_id", "google_location_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("google_connections.id", ondelete="SET NULL"), nullable=True
    )
    external_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("external_accounts.id", ondelete="SET NULL"), nullable=True
    )

    # Both identity forms are kept: v1 APIs use "locations/123" while the legacy
    # v4 API needs the account-qualified "accounts/1/locations/2".
    google_location_name: Mapped[str] = mapped_column(String(255))
    source_location_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    google_resource_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    place_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    store_code: Mapped[str | None] = mapped_column(String(128), nullable=True)

    title: Mapped[str] = mapped_column(String(320))
    primary_category_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_category_display: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_lines: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    locality: Mapped[str | None] = mapped_column(String(160), nullable=True)
    administrative_area: Mapped[str | None] = mapped_column(String(160), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone_primary: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    open_status: Mapped[OpenStatus | None] = mapped_column(
        Enum(OpenStatus, name="open_status"), nullable=True
    )
    opening_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    has_voice_of_merchant: Mapped[bool] = mapped_column(Boolean, default=False)
    has_pending_edits: Mapped[bool] = mapped_column(Boolean, default=False)
    has_google_updated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    maps_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    new_review_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    source: Mapped[LocationSource] = mapped_column(
        Enum(LocationSource, name="location_source"), default=LocationSource.google
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    categories: Mapped[list["LocationCategory"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    hours_periods: Mapped[list["LocationHoursPeriod"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )
    attributes: Mapped[list["LocationAttributeValue"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class LocationCategory(Base):
    __tablename__ = "location_categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    category_name: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    location: Mapped[Location] = relationship(back_populates="categories")


class LocationHoursPeriod(Base):
    """One Google opening period. Google allows several periods per day and
    overnight spans, so these are never collapsed to one row per weekday."""

    __tablename__ = "location_hours_periods"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    hours_type: Mapped[str] = mapped_column(String(32), default="REGULAR")
    open_day: Mapped[str] = mapped_column(String(16))
    open_hour: Mapped[int] = mapped_column(Integer)
    open_minute: Mapped[int] = mapped_column(Integer, default=0)
    close_day: Mapped[str] = mapped_column(String(16))
    close_hour: Mapped[int] = mapped_column(Integer)
    close_minute: Mapped[int] = mapped_column(Integer, default=0)

    location: Mapped[Location] = relationship(back_populates="hours_periods")


class LocationAttributeValue(Base):
    """Google attributes are typed (BOOL / ENUM / REPEATED_ENUM / URL), so the
    value is stored as JSON rather than a scalar string."""

    __tablename__ = "location_attribute_values"
    __table_args__ = (UniqueConstraint("location_id", "attribute_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    attribute_id: Mapped[str] = mapped_column(String(255))
    value_type: Mapped[str] = mapped_column(String(32))
    values: Mapped[Any] = mapped_column(JSON)

    location: Mapped[Location] = relationship(back_populates="attributes")


class AttributeCatalogItem(TimestampMixin, Base):
    """One attribute available for this organization's business category."""

    __tablename__ = "attribute_catalog_items"
    __table_args__ = (UniqueConstraint("organization_id", "external_attribute_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    external_attribute_id: Mapped[str] = mapped_column(String(64))
    attribute_name: Mapped[str] = mapped_column(String(255))
    attribute_group: Mapped[str] = mapped_column(String(64))
    applies_to_category: Mapped[str] = mapped_column(String(255))
    value_type: Mapped[str] = mapped_column(String(32))
