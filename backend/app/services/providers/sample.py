"""Sample provider — the whole Business Profile pipeline, fed from the sample CSVs.

Google never approved this Cloud project for Business Profile API access: every live read
came back `429 RESOURCE_EXHAUSTED` with `quota_limit_value: 0`. This provider is therefore
the only one, and it serves the sample dataset behind the `GbpProvider` protocol so profile
reads and edits still run their real code paths over real-shaped data.

It stays honest about that: locations arrive tagged `LocationSource.fixture`, which the API
and UI surface as a "Sample data" label.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from app.models import LocationSource
from app.services.providers.base import (
    LocationChanges,
    ProviderAccount,
    ProviderCategory,
    ProviderLocation,
    UpdateResult,
    build_update_mask,
    validate_changes,
)
from app.services.providers.sample_data import SAMPLE_ACCOUNT, load_locations

if TYPE_CHECKING:
    from app.models import GoogleConnection, Location

# Edits committed against the sample dataset, keyed by Google location name. The CSVs are
# read-only, so a write lands here and is replayed over the parsed location on every read.
# Process-local by design: this is a demo of the round trip, not a second database.
_edits: dict[str, dict[str, Any]] = {}


def _replace_primary_category(
    categories: tuple[ProviderCategory, ...], primary: ProviderCategory
) -> tuple[ProviderCategory, ...]:
    """Swap the primary category, keeping the additional ones Google would keep."""
    return (
        replace(primary, is_primary=True),
        *(item for item in categories if not item.is_primary),
    )


def _record(location_name: str, changes: LocationChanges) -> None:
    edit = _edits.setdefault(location_name, {})
    for field in ("title", "phone_primary", "website_uri", "description", "open_status"):
        value = getattr(changes, field)
        if value is not None:
            edit[field] = value
    if changes.hours_periods is not None:
        edit["hours_periods"] = tuple(changes.hours_periods)
    if changes.attributes is not None:
        edit["attributes"] = tuple(changes.attributes)
    if changes.primary_category is not None:
        edit["primary_category"] = changes.primary_category


def _apply_edits(location: ProviderLocation) -> ProviderLocation:
    edit = _edits.get(location.google_location_name)
    if not edit:
        return location
    fields = {key: value for key, value in edit.items() if key != "primary_category"}
    primary: ProviderCategory | None = edit.get("primary_category")
    if primary is not None:
        fields["primary_category_name"] = primary.category_name
        fields["primary_category_display"] = primary.display_name
        fields["categories"] = _replace_primary_category(location.categories, primary)
    return replace(location, **fields)


def forget_edits() -> None:
    """Drop every in-process edit, returning the dataset to what the CSVs say."""
    _edits.clear()


class SampleGbpProvider:
    """Serves the sample dataset through the `GbpProvider` protocol."""

    name = "sample"
    location_source = LocationSource.fixture

    async def list_accounts(self, connection: GoogleConnection) -> list[ProviderAccount]:
        del connection  # the sample dataset is the same for every connected account
        return [SAMPLE_ACCOUNT]

    async def list_locations(
        self, connection: GoogleConnection, account_resource_name: str
    ) -> list[ProviderLocation]:
        del connection
        if account_resource_name and account_resource_name != SAMPLE_ACCOUNT.resource_name:
            return []
        return [_apply_edits(location) for location in load_locations()]

    async def update_location(
        self,
        connection: GoogleConnection | None,
        location: Location,
        changes: LocationChanges,
        *,
        validate_only: bool,
    ) -> UpdateResult:
        """Validate against the shared field rules, then mutate the in-process copy.

        The rules in `providers.base` are the ones Google itself enforces, so a preview
        here fails on the same input Google would have rejected.
        """
        del connection
        mask = build_update_mask(changes)
        if not mask:
            return UpdateResult(ok=False, error="No fields to update")

        errors = validate_changes(changes)
        if errors:
            return UpdateResult(ok=False, field_errors=errors, applied_mask=mask)

        if not validate_only:
            _record(location.google_location_name, changes)

        return UpdateResult(
            ok=True,
            applied_mask=mask,
            response={
                "provider": self.name,
                "name": location.google_location_name,
                "updateMask": ",".join(mask),
                "validateOnly": validate_only,
            },
        )
