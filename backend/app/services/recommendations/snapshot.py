"""Read each tenant's data into plain immutable-by-convention analysis inputs."""

import hashlib
import json
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.models import Location, ProjectLocation, TrackedKeyword
from app.services.recommendations.contracts import EXCLUDED, TABLES


def scalar(value):
    if isinstance(value, (date, datetime, UUID)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value


def fingerprint(snapshot: dict) -> str:
    serialized = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode()).hexdigest()


async def read_snapshot(
    db: AsyncSession, organization_id: UUID, location_id: UUID | None = None
) -> dict:
    """Read one location's analysis inputs, or the whole organization's when unscoped.

    An audit is about a single business profile, so the snapshot behind it holds only
    that profile's rows. The attribute catalog stays organization-wide because it is a
    shared vocabulary, not the location's own data.
    """
    # Auth may already have started the request transaction. Use a dedicated
    # repeatable-read transaction so imports cannot interleave the table reads.
    if isinstance(db.bind, AsyncEngine) and db.bind.dialect.name == "postgresql":
        bound = db.bind.execution_options(isolation_level="REPEATABLE READ")
        async with AsyncSession(bound) as snapshot_db:
            return await _read_snapshot(snapshot_db, organization_id, location_id)
    return await _read_snapshot(db, organization_id, location_id)


def _scope(name: str, model, statement, organization_id: UUID, location_id: UUID | None):
    if name == "projects":
        statement = statement.where(model.organization_id == organization_id)
        if location_id is None:
            return statement
        return statement.where(
            model.id.in_(
                select(ProjectLocation.project_id).where(ProjectLocation.location_id == location_id)
            )
        )
    if hasattr(model, "organization_id"):
        statement = statement.where(model.organization_id == organization_id)
    else:
        statement = statement.join(Location, Location.id == model.location_id).where(
            Location.organization_id == organization_id
        )
    if location_id is None:
        return statement
    if name == "locations":
        return statement.where(model.id == location_id)
    if name == "catalog":
        # A shared vocabulary of available attributes, not rows belonging to a location.
        return statement
    if name == "competitors":
        # Reached through the location's tracked keywords; it carries no location of its own.
        return statement.where(
            model.tracked_keyword_id.in_(
                select(TrackedKeyword.id).where(TrackedKeyword.location_id == location_id)
            )
        )
    return statement.where(model.location_id == location_id)


async def _read_snapshot(
    db: AsyncSession, organization_id: UUID, location_id: UUID | None = None
) -> dict:
    snapshot = {}
    for name, model in TABLES.items():
        statement = _scope(name, model, select(model), organization_id, location_id)
        rows = (await db.scalars(statement.order_by(model.id))).all()
        snapshot[name] = [
            {
                c.key: scalar(getattr(row, c.key))
                for c in model.__table__.columns
                if c.key not in EXCLUDED
            }
            for row in rows
        ]
    return snapshot
