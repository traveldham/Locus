"""Persistence helpers for writing provider data into our tables.

Every write here is an upsert keyed on a natural Google identifier, which is what makes
`app.seed` safe to run over and over.
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ExternalAccount,
    GoogleConnection,
    Location,
    LocationAttributeValue,
    LocationCategory,
    LocationHoursPeriod,
    LocationSource,
    Project,
    ProjectLocation,
)
from app.services.providers import ProviderAccount, ProviderLocation


async def upsert_external_accounts(
    db: AsyncSession, connection: GoogleConnection, accounts: list[ProviderAccount]
) -> list[ExternalAccount]:
    result = await db.execute(
        select(ExternalAccount).where(ExternalAccount.connection_id == connection.id)
    )
    existing = {row.resource_name: row for row in result.scalars()}

    stored: list[ExternalAccount] = []
    for account in accounts:
        row = existing.get(account.resource_name)
        if row is None:
            row = ExternalAccount(connection_id=connection.id, resource_name=account.resource_name)
            db.add(row)
        row.account_name = account.account_name
        row.account_type = account.account_type
        row.role = account.role
        row.verification_state = account.verification_state
        stored.append(row)
    await db.flush()
    return stored


async def upsert_location(
    db: AsyncSession,
    *,
    organization_id: UUID,
    connection: GoogleConnection,
    external_account_id: UUID | None,
    payload: ProviderLocation,
    source: LocationSource,
    synced_at: datetime,
) -> Location:
    """Create or refresh one location, unique on (organization_id, google_location_name)."""
    result = await db.execute(
        select(Location)
        .options(
            selectinload(Location.categories),
            selectinload(Location.hours_periods),
            selectinload(Location.attributes),
        )
        .where(
            Location.organization_id == organization_id,
            Location.google_location_name == payload.google_location_name,
        )
    )
    location = result.scalar_one_or_none()
    is_new = location is None
    if location is None:
        location = Location(
            organization_id=organization_id,
            google_location_name=payload.google_location_name,
        )
        db.add(location)

    location.connection_id = connection.id
    location.external_account_id = external_account_id
    location.google_resource_name = payload.google_resource_name
    location.place_id = payload.place_id
    location.store_code = payload.store_code
    location.title = payload.title
    location.primary_category_name = payload.primary_category_name
    location.primary_category_display = payload.primary_category_display
    location.address_lines = list(payload.address_lines) or None
    location.locality = payload.locality
    location.administrative_area = payload.administrative_area
    location.postal_code = payload.postal_code
    location.region_code = payload.region_code
    location.latitude = payload.latitude
    location.longitude = payload.longitude
    location.phone_primary = payload.phone_primary
    location.website_uri = payload.website_uri
    location.description = payload.description
    location.open_status = payload.open_status
    location.opening_date = payload.opening_date
    location.has_voice_of_merchant = payload.has_voice_of_merchant
    location.has_pending_edits = payload.has_pending_edits
    location.has_google_updated = payload.has_google_updated
    location.is_duplicate = payload.is_duplicate
    location.maps_uri = payload.maps_uri
    location.new_review_uri = payload.new_review_uri
    location.source = source
    location.last_synced_at = synced_at

    # Children are replaced wholesale: Google is the source of truth, so a category or
    # opening period it dropped must disappear here too. The flush in between emits the
    # DELETEs before the re-INSERTs, keeping the attribute unique constraint happy. A
    # brand-new location has nothing to clear — and clearing it would leave the
    # collections unloaded, tripping a lazy load after the flush.
    if not is_new:
        location.categories.clear()
        location.hours_periods.clear()
        location.attributes.clear()
        await db.flush()

    location.categories.extend(
        LocationCategory(
            category_name=item.category_name,
            display_name=item.display_name,
            is_primary=item.is_primary,
        )
        for item in payload.categories
    )
    location.hours_periods.extend(
        LocationHoursPeriod(
            hours_type=item.hours_type,
            open_day=item.open_day,
            open_hour=item.open_hour,
            open_minute=item.open_minute,
            close_day=item.close_day,
            close_hour=item.close_hour,
            close_minute=item.close_minute,
        )
        for item in payload.hours_periods
    )
    seen: set[str] = set()
    for item in payload.attributes:
        if item.attribute_id in seen:
            continue
        seen.add(item.attribute_id)
        location.attributes.append(
            LocationAttributeValue(
                attribute_id=item.attribute_id,
                value_type=item.value_type,
                values=list(item.values),
            )
        )
    await db.flush()
    return location


async def link_locations_to_project(
    db: AsyncSession, project: Project, locations: list[Location]
) -> None:
    """Attach locations to a project without duplicating existing links."""
    result = await db.execute(
        select(ProjectLocation.location_id).where(ProjectLocation.project_id == project.id)
    )
    linked = set(result.scalars())
    for location in locations:
        if location.id in linked:
            continue
        linked.add(location.id)
        db.add(ProjectLocation(project_id=project.id, location_id=location.id))
    await db.flush()


async def unique_project_slug(db: AsyncSession, organization_id: UUID, name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"
    candidate = base
    number = 2
    while await db.scalar(
        select(Project.id).where(
            Project.organization_id == organization_id, Project.slug == candidate
        )
    ):
        candidate = f"{base}-{number}"
        number += 1
    return candidate
