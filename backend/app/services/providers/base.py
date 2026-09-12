"""Provider-neutral shapes for Google Business Profile data.

Everything above this layer talks to these plain dataclasses instead of Google JSON, so
the API and persistence code never has to parse a Google response shape.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from urllib.parse import urlparse

from app.models import LocationSource, OpenStatus

if TYPE_CHECKING:
    from app.models import GoogleConnection, Location


@dataclass(frozen=True, slots=True)
class ProviderAccount:
    """A Google Business Profile account (`accounts/123456`)."""

    resource_name: str
    account_name: str
    account_type: str | None = None
    role: str | None = None
    verification_state: str | None = None


@dataclass(frozen=True, slots=True)
class ProviderCategory:
    category_name: str
    display_name: str | None = None
    is_primary: bool = False


@dataclass(frozen=True, slots=True)
class ProviderHoursPeriod:
    open_day: str
    open_hour: int
    close_day: str
    close_hour: int
    open_minute: int = 0
    close_minute: int = 0
    hours_type: str = "REGULAR"


@dataclass(frozen=True, slots=True)
class ProviderAttribute:
    """Google attributes are typed (BOOL / ENUM / REPEATED_ENUM / URL)."""

    attribute_id: str
    value_type: str
    values: tuple[Any, ...] = ()


@dataclass(frozen=True, slots=True)
class ProviderLocation:
    """One business location, mirroring the fields of `app.models.location.Location`."""

    google_location_name: str
    title: str
    google_resource_name: str | None = None
    place_id: str | None = None
    store_code: str | None = None
    primary_category_name: str | None = None
    primary_category_display: str | None = None
    address_lines: tuple[str, ...] = ()
    locality: str | None = None
    administrative_area: str | None = None
    postal_code: str | None = None
    region_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone_primary: str | None = None
    website_uri: str | None = None
    description: str | None = None
    open_status: OpenStatus | None = None
    opening_date: date | None = None
    has_voice_of_merchant: bool = False
    has_pending_edits: bool = False
    has_google_updated: bool = False
    is_duplicate: bool = False
    maps_uri: str | None = None
    new_review_uri: str | None = None
    categories: tuple[ProviderCategory, ...] = field(default_factory=tuple)
    hours_periods: tuple[ProviderHoursPeriod, ...] = field(default_factory=tuple)
    attributes: tuple[ProviderAttribute, ...] = field(default_factory=tuple)


class ProviderError(RuntimeError):
    """A provider could not fulfil a read — surfaced to the API as a 4xx/5xx, never a crash."""


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

# Canonical order of the editable fields. The update mask is built in this order so a
# preview, an audit row and the request actually sent to Google always read the same.
EDITABLE_FIELDS: tuple[str, ...] = (
    "title",
    "phone_primary",
    "website_uri",
    "description",
    "open_status",
    "hours_periods",
    "attributes",
    "primary_category",
)

# Our neutral field name -> the Google Business Information field path used in updateMask.
# `updateMask` is REQUIRED on locations.patch: Google treats a patch without it as a full
# replace and unsets every field left out, so the mask must name only what really changed.
UPDATE_MASK_PATHS: dict[str, str] = {
    "title": "title",
    "phone_primary": "phoneNumbers",
    "website_uri": "websiteUri",
    "description": "profile",
    "open_status": "openInfo",
    "hours_periods": "regularHours",
    "attributes": "attributes",
    "primary_category": "categories",
}

DAYS_OF_WEEK = frozenset(
    {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"}
)

TITLE_MAX_LENGTH = 320
DESCRIPTION_MAX_LENGTH = 750
MIN_PHONE_DIGITS = 7


@dataclass(frozen=True, slots=True)
class LocationChanges:
    """Exactly the fields the user edited.

    `None` means "untouched" and keeps the field out of the update mask — it never means
    "clear it". Clearing is an empty string, which is a real change Google is asked to make.
    """

    title: str | None = None
    phone_primary: str | None = None
    website_uri: str | None = None
    description: str | None = None
    open_status: OpenStatus | None = None
    hours_periods: tuple[ProviderHoursPeriod, ...] | None = None
    attributes: tuple[ProviderAttribute, ...] | None = None
    primary_category: ProviderCategory | None = None

    def changed_fields(self) -> tuple[str, ...]:
        return tuple(name for name in EDITABLE_FIELDS if getattr(self, name) is not None)

    @property
    def is_empty(self) -> bool:
        return not self.changed_fields()


@dataclass(frozen=True, slots=True)
class UpdateResult:
    """The outcome of one write attempt, whether it was a dry run or the real thing."""

    ok: bool
    field_errors: dict[str, str] = field(default_factory=dict)
    applied_mask: list[str] = field(default_factory=list)
    response: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def build_update_mask(changes: LocationChanges) -> list[str]:
    """The comma-separated `updateMask` Google requires, derived only from real changes."""
    return [UPDATE_MASK_PATHS[name] for name in changes.changed_fields()]


def _validate_url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "Enter a full website address starting with http:// or https://."
    return None


def _validate_period(period: ProviderHoursPeriod) -> str | None:
    if period.open_day.upper() not in DAYS_OF_WEEK or period.close_day.upper() not in DAYS_OF_WEEK:
        return "Opening periods must use weekday names such as MONDAY."
    if not 0 <= period.open_hour <= 23 or not 0 <= period.open_minute <= 59:
        return "Opening times must be between 00:00 and 23:59."
    # Google writes a period that ends at midnight as 24:00, so 24 is allowed on close only.
    if not 0 <= period.close_hour <= 24 or not 0 <= period.close_minute <= 59:
        return "Closing times must be between 00:00 and 24:00."
    if period.close_hour == 24 and period.close_minute:
        return "Closing times must be between 00:00 and 24:00."
    if period.open_day.upper() != period.close_day.upper():
        return None  # an overnight span legitimately closes on the following day
    if period.close_hour * 60 + period.close_minute <= period.open_hour * 60 + period.open_minute:
        return "Closing time must be after opening time on the same day."
    return None


def validate_changes(changes: LocationChanges) -> dict[str, str]:
    """Field-level validation, so a dry run fails on exactly what Google would reject.

    Returns `{our_field_name: message}`, the shape the UI renders.
    """
    errors: dict[str, str] = {}

    if changes.title is not None:
        title = changes.title.strip()
        if not title:
            errors["title"] = "Business name is required."
        elif len(title) > TITLE_MAX_LENGTH:
            errors["title"] = f"Business name must be {TITLE_MAX_LENGTH} characters or fewer."

    # An empty string clears the field, which is allowed; anything else must be plausible.
    if changes.phone_primary:
        digits = re.sub(r"\D", "", changes.phone_primary)
        if len(digits) < MIN_PHONE_DIGITS:
            errors["phone_primary"] = (
                f"Enter a phone number with at least {MIN_PHONE_DIGITS} digits."
            )

    if changes.website_uri:
        message = _validate_url(changes.website_uri.strip())
        if message:
            errors["website_uri"] = message

    if changes.description and len(changes.description.strip()) > DESCRIPTION_MAX_LENGTH:
        errors["description"] = f"Description must be {DESCRIPTION_MAX_LENGTH} characters or fewer."

    if changes.hours_periods is not None:
        for period in changes.hours_periods:
            message = _validate_period(period)
            if message:
                errors["hours_periods"] = message
                break

    if changes.attributes is not None:
        for attribute in changes.attributes:
            if not attribute.attribute_id.strip():
                errors["attributes"] = "Every attribute needs an identifier."
                break
            if not attribute.value_type.strip():
                errors["attributes"] = f"{attribute.attribute_id} is missing a value type."
                break

    if changes.primary_category is not None and not changes.primary_category.category_name.strip():
        errors["primary_category"] = "Choose a primary category."

    return errors


@runtime_checkable
class GbpProvider(Protocol):
    """The only Business Profile surface the API layer knows about."""

    name: str
    location_source: LocationSource

    async def list_accounts(self, connection: GoogleConnection) -> list[ProviderAccount]: ...

    async def list_locations(
        self, connection: GoogleConnection, account_resource_name: str
    ) -> list[ProviderLocation]: ...

    async def update_location(
        self,
        connection: GoogleConnection | None,
        location: Location,
        changes: LocationChanges,
        *,
        validate_only: bool,
    ) -> UpdateResult:
        """Write `changes` to one profile.

        `validate_only=True` is the preview: Google runs the identical request and reports
        the same field errors without committing anything. Nothing reaches a merchant's live
        profile until the caller repeats the call with `validate_only=False`.
        """
        ...
