"""Working out what a profile edit actually changes, and writing it back locally.

Two jobs live here, both kept out of the router.

**Planning.** The diff is computed server-side by comparing the request against the stored
`Location`. A client never supplies the update mask: `locations.patch` treats any field
omitted from the mask as *unset*, so a mask that named a field the user never touched would
quietly wipe it. Deriving the mask from a real diff makes that impossible.

**Persisting.** The local copy is only touched after Google confirms the write, so our
database never claims a change that a merchant's live profile does not have.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Location,
    LocationAttributeValue,
    LocationCategory,
    LocationHoursPeriod,
    OpenStatus,
)
from app.schemas.locations import (
    AttributeInput,
    CategoryInput,
    FieldChange,
    HoursPeriodInput,
    LocationEditRequest,
)
from app.services.providers import (
    LocationChanges,
    ProviderAttribute,
    ProviderCategory,
    ProviderHoursPeriod,
    build_update_mask,
)

REGULAR_HOURS = "REGULAR"

FIELD_LABELS: dict[str, str] = {
    "title": "Business name",
    "phone_primary": "Primary phone",
    "website_uri": "Website",
    "description": "Description",
    "open_status": "Open status",
    "hours_periods": "Regular hours",
    "attributes": "Attributes",
    "primary_category": "Primary category",
}

TEXT_FIELDS: tuple[str, ...] = ("title", "phone_primary", "website_uri", "description")


@dataclass(frozen=True, slots=True)
class EditPlan:
    """What would be sent, why, and under which mask."""

    changes: LocationChanges
    field_changes: list[FieldChange]
    mask: list[str]

    @property
    def is_empty(self) -> bool:
        return not self.mask


def _text(value: str | None) -> str | None:
    """Compare text the way a person would: blank and absent are the same thing."""
    if value is None:
        return None
    return value.strip() or None


def _period_tuple(
    period: HoursPeriodInput | LocationHoursPeriod,
) -> tuple[str, int, int, str, int, int]:
    return (
        period.open_day.upper(),
        period.open_hour,
        period.open_minute,
        period.close_day.upper(),
        period.close_hour,
        period.close_minute,
    )


def _period_json(period: tuple[str, int, int, str, int, int]) -> dict[str, Any]:
    open_day, open_hour, open_minute, close_day, close_hour, close_minute = period
    return {
        "open_day": open_day,
        "open_hour": open_hour,
        "open_minute": open_minute,
        "close_day": close_day,
        "close_hour": close_hour,
        "close_minute": close_minute,
    }


def _stored_periods(location: Location) -> list[tuple[str, int, int, str, int, int]]:
    return sorted(
        _period_tuple(period)
        for period in location.hours_periods
        if period.hours_type == REGULAR_HOURS
    )


def _attribute_tuple(value_type: str, values: Any) -> tuple[str, list[Any]]:
    return value_type.upper(), list(values or [])


def _attribute_json(attribute_id: str, value_type: str, values: list[Any]) -> dict[str, Any]:
    return {"attribute_id": attribute_id, "value_type": value_type, "values": values}


def _category_json(category_name: str | None, display_name: str | None) -> dict[str, Any] | None:
    if not category_name:
        return None
    return {"category_name": category_name, "display_name": display_name}


def _plan_text_fields(
    location: Location, payload: LocationEditRequest, provided: set[str]
) -> tuple[dict[str, Any], list[FieldChange]]:
    values: dict[str, Any] = {}
    field_changes: list[FieldChange] = []
    for name in TEXT_FIELDS:
        if name not in provided:
            continue
        current = _text(getattr(location, name))
        proposed = _text(getattr(payload, name))
        if current == proposed:
            continue
        # `None` would read as "untouched" further down, so a deliberate clear is sent to
        # Google as an empty string.
        values[name] = proposed if proposed is not None else ""
        field_changes.append(
            FieldChange(field=name, label=FIELD_LABELS[name], current=current, proposed=proposed)
        )
    return values, field_changes


def _plan_hours(
    location: Location, submitted: list[HoursPeriodInput]
) -> tuple[tuple[ProviderHoursPeriod, ...], FieldChange] | None:
    current = _stored_periods(location)
    proposed = sorted(_period_tuple(period) for period in submitted)
    if current == proposed:
        return None
    periods = tuple(
        ProviderHoursPeriod(
            open_day=period.open_day.upper(),
            open_hour=period.open_hour,
            open_minute=period.open_minute,
            close_day=period.close_day.upper(),
            close_hour=period.close_hour,
            close_minute=period.close_minute,
        )
        for period in submitted
    )
    return periods, FieldChange(
        field="hours_periods",
        label=FIELD_LABELS["hours_periods"],
        current=[_period_json(period) for period in current],
        proposed=[_period_json(period) for period in proposed],
    )


def _plan_attributes(
    location: Location, submitted: list[AttributeInput]
) -> tuple[tuple[ProviderAttribute, ...], FieldChange] | None:
    """Attributes carry their own mask, so only the ones that really differ are sent."""
    stored = {
        row.attribute_id: _attribute_tuple(row.value_type, row.values)
        for row in location.attributes
    }
    changed: list[AttributeInput] = []
    current_json: list[dict[str, Any]] = []
    proposed_json: list[dict[str, Any]] = []
    for item in submitted:
        proposed = _attribute_tuple(item.value_type, item.values)
        if stored.get(item.attribute_id) == proposed:
            continue
        changed.append(item)
        existing = stored.get(item.attribute_id)
        if existing is not None:
            current_json.append(_attribute_json(item.attribute_id, *existing))
        proposed_json.append(_attribute_json(item.attribute_id, *proposed))
    if not changed:
        return None
    attributes = tuple(
        ProviderAttribute(
            attribute_id=item.attribute_id,
            value_type=item.value_type.upper(),
            values=tuple(item.values),
        )
        for item in changed
    )
    return attributes, FieldChange(
        field="attributes",
        label=FIELD_LABELS["attributes"],
        current=current_json,
        proposed=proposed_json,
    )


def _plan_category(
    location: Location, submitted: CategoryInput
) -> tuple[ProviderCategory, FieldChange] | None:
    # Only the category id is compared: the display name is Google's own rendering of it,
    # so a differing label alone is not a change worth sending.
    if _text(location.primary_category_name) == _text(submitted.category_name):
        return None
    category = ProviderCategory(
        category_name=submitted.category_name.strip(),
        display_name=submitted.display_name,
        is_primary=True,
    )
    return category, FieldChange(
        field="primary_category",
        label=FIELD_LABELS["primary_category"],
        current=_category_json(location.primary_category_name, location.primary_category_display),
        proposed=_category_json(category.category_name, category.display_name),
    )


def plan_edit(location: Location, payload: LocationEditRequest) -> EditPlan:
    """Diff the request against the stored location; the mask falls out of the diff."""
    provided = payload.model_fields_set
    values, field_changes = _plan_text_fields(location, payload, provided)

    if "open_status" in provided and payload.open_status != location.open_status:
        values["open_status"] = payload.open_status
        field_changes.append(
            FieldChange(
                field="open_status",
                label=FIELD_LABELS["open_status"],
                current=location.open_status.value if location.open_status else None,
                proposed=payload.open_status.value if payload.open_status else None,
            )
        )

    if "hours_periods" in provided and payload.hours_periods is not None:
        planned = _plan_hours(location, payload.hours_periods)
        if planned is not None:
            values["hours_periods"], change = planned
            field_changes.append(change)

    if "attributes" in provided and payload.attributes is not None:
        planned = _plan_attributes(location, payload.attributes)
        if planned is not None:
            values["attributes"], change = planned
            field_changes.append(change)

    if "primary_category" in provided and payload.primary_category is not None:
        planned = _plan_category(location, payload.primary_category)
        if planned is not None:
            values["primary_category"], change = planned
            field_changes.append(change)

    changes = LocationChanges(**values)
    return EditPlan(changes=changes, field_changes=field_changes, mask=build_update_mask(changes))


async def apply_locally(db: AsyncSession, location: Location, changes: LocationChanges) -> None:
    """Mirror a *confirmed* Google write into our copy. Never call before Google says ok."""
    if changes.title is not None:
        location.title = changes.title.strip()
    if changes.phone_primary is not None:
        location.phone_primary = _text(changes.phone_primary)
    if changes.website_uri is not None:
        location.website_uri = _text(changes.website_uri)
    if changes.description is not None:
        location.description = _text(changes.description)
    if changes.open_status is not None:
        location.open_status = OpenStatus(changes.open_status)

    if changes.primary_category is not None:
        location.primary_category_name = changes.primary_category.category_name
        location.primary_category_display = changes.primary_category.display_name
        primary = next((row for row in location.categories if row.is_primary), None)
        if primary is None:
            location.categories.append(
                LocationCategory(
                    category_name=changes.primary_category.category_name,
                    display_name=changes.primary_category.display_name,
                    is_primary=True,
                )
            )
        else:
            primary.category_name = changes.primary_category.category_name
            primary.display_name = changes.primary_category.display_name

    if changes.hours_periods is not None:
        # `regularHours` is replaced wholesale by the patch, so the stored regular periods
        # are too — special hours, which this edit never touches, are left alone. The flush
        # in between orders the DELETEs ahead of the re-INSERTs.
        for period in [row for row in location.hours_periods if row.hours_type == REGULAR_HOURS]:
            location.hours_periods.remove(period)
        await db.flush()
        location.hours_periods.extend(
            LocationHoursPeriod(
                hours_type=REGULAR_HOURS,
                open_day=period.open_day,
                open_hour=period.open_hour,
                open_minute=period.open_minute,
                close_day=period.close_day,
                close_hour=period.close_hour,
                close_minute=period.close_minute,
            )
            for period in changes.hours_periods
        )

    if changes.attributes is not None:
        # `attributeMask` names exactly the attributes that were written, so the rest of the
        # location's attributes survive untouched here as well.
        existing = {row.attribute_id: row for row in location.attributes}
        for item in changes.attributes:
            row = existing.get(item.attribute_id)
            if row is None:
                location.attributes.append(
                    LocationAttributeValue(
                        attribute_id=item.attribute_id,
                        value_type=item.value_type,
                        values=list(item.values),
                    )
                )
            else:
                row.value_type = item.value_type
                row.values = list(item.values)

    await db.flush()
