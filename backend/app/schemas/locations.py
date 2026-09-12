from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import ActionStatus, LocationSource, OpenStatus


class LocationCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_name: str
    display_name: str | None = None
    is_primary: bool = False


class LocationHoursPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hours_type: str = "REGULAR"
    open_day: str
    open_hour: int
    open_minute: int = 0
    close_day: str
    close_hour: int
    close_minute: int = 0


class LocationAttributeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attribute_id: str
    value_type: str
    values: Any = None


class AttributeCatalogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_attribute_id: str
    attribute_name: str
    attribute_group: str
    applies_to_category: str
    value_type: str


class AttributeCatalogResponse(BaseModel):
    items: list[AttributeCatalogItemResponse] = []
    total: int = 0


class LocationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    google_location_name: str
    title: str
    store_code: str | None = None
    primary_category_display: str | None = None
    address: str | None = None
    locality: str | None = None
    administrative_area: str | None = None
    open_status: OpenStatus | None = None
    has_voice_of_merchant: bool = False
    has_pending_edits: bool = False
    has_google_updated: bool = False
    is_duplicate: bool = False
    # Where this profile came from. `fixture` is the sample dataset served while Google
    # has not approved API access, and the UI labels it as such on every row.
    source: LocationSource = LocationSource.google
    last_synced_at: datetime | None = None


class LocationDetail(LocationSummary):
    model_config = ConfigDict(from_attributes=True)

    google_resource_name: str | None = None
    source_location_id: str | None = None
    place_id: str | None = None
    primary_category_name: str | None = None
    address_lines: list[str] | None = None
    postal_code: str | None = None
    region_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    phone_primary: str | None = None
    website_uri: str | None = None
    description: str | None = None
    opening_date: date | None = None
    maps_uri: str | None = None
    new_review_uri: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    categories: list[LocationCategoryResponse] = []
    hours_periods: list[LocationHoursPeriodResponse] = []
    attributes: list[LocationAttributeResponse] = []


# ---------------------------------------------------------------------------
# Editing a profile
# ---------------------------------------------------------------------------


class HoursPeriodInput(BaseModel):
    """One opening period. Sending `hours_periods` replaces the whole regular schedule,
    which is what Google's `regularHours` field does."""

    open_day: str
    open_hour: Annotated[int, Field(ge=0, le=23)]
    open_minute: Annotated[int, Field(ge=0, le=59)] = 0
    close_day: str
    close_hour: Annotated[int, Field(ge=0, le=24)]
    close_minute: Annotated[int, Field(ge=0, le=59)] = 0


class AttributeInput(BaseModel):
    attribute_id: str
    value_type: str = "BOOL"
    values: list[Any] = []


class CategoryInput(BaseModel):
    category_name: str
    display_name: str | None = None


class LocationEditRequest(BaseModel):
    """Every field is optional, and *omitted* is meaningfully different from *null*.

    Only the fields actually present in the request body are considered; the diff against
    the stored location decides what ends up in the update mask. A client cannot ask for a
    field it did not send to be touched, which is what keeps an unrelated field from being
    unset by a patch.
    """

    title: str | None = None
    phone_primary: str | None = None
    website_uri: str | None = None
    description: str | None = None
    open_status: OpenStatus | None = None
    hours_periods: list[HoursPeriodInput] | None = None
    attributes: list[AttributeInput] | None = None
    primary_category: CategoryInput | None = None


class FieldChange(BaseModel):
    field: str
    label: str
    current: Any = None
    proposed: Any = None


class EditPreviewResponse(BaseModel):
    """The dry run. `valid` is true only when there is something to send and Google
    accepted the request with `validateOnly=true`."""

    changes: list[FieldChange] = []
    update_mask: list[str] = []
    field_errors: dict[str, str] = {}
    valid: bool = False


class ActionUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None = None


class ProfileActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action_type: str
    status: ActionStatus
    payload: Any = None
    error: str | None = None
    created_at: datetime
    user: ActionUser | None = None
