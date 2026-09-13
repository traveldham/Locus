import re
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DbSession
from app.api.locations import serialize_summary
from app.api.scoping import OrganizationId
from app.models import GoogleConnection, Location, Project, ProjectLocation, ProjectStatus
from app.schemas import (
    LocationSummary,
    MessageResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectLocationsRequest,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.recommendations.queue import enqueue_audits

router = APIRouter(prefix="/projects", tags=["Projects"])

SLUG_MAX = 90


def serialize_project(project: Project, location_count: int) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        status=project.status,
        location_count=location_count,
        created_at=project.created_at,
    )


def serialize_detail(project: Project, locations: list[LocationSummary]) -> ProjectDetailResponse:
    return ProjectDetailResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        status=project.status,
        location_count=len(locations),
        created_at=project.created_at,
        google_connection_id=project.google_connection_id,
        locations=locations,
    )


async def unique_slug(db: DbSession, organization_id: UUID, name: str) -> str:
    """Slugs only need to be unique per organization, per the table constraint."""
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:SLUG_MAX] or "project"
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


async def owned_project(db: DbSession, organization_id: UUID, project_id: UUID) -> Project:
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.organization_id == organization_id)
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def owned_location_ids(
    db: DbSession, organization_id: UUID, location_ids: Sequence[UUID]
) -> list[UUID]:
    wanted = list(dict.fromkeys(location_ids))
    if not wanted:
        return []
    result = await db.execute(
        select(Location.id).where(
            Location.organization_id == organization_id, Location.id.in_(wanted)
        )
    )
    found = set(result.scalars().all())
    missing = [str(location_id) for location_id in wanted if location_id not in found]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Locations not found in this organization: {', '.join(missing)}",
        )
    return wanted


async def link_locations(db: DbSession, project_id: UUID, location_ids: Sequence[UUID]) -> None:
    """Idempotent: re-adding a linked location is a no-op, never a duplicate row."""
    if not location_ids:
        return
    result = await db.execute(
        select(ProjectLocation.location_id).where(
            ProjectLocation.project_id == project_id,
            ProjectLocation.location_id.in_(location_ids),
        )
    )
    linked = set(result.scalars().all())
    db.add_all(
        [
            ProjectLocation(project_id=project_id, location_id=location_id)
            for location_id in location_ids
            if location_id not in linked
        ]
    )


async def project_locations(db: DbSession, project_id: UUID) -> list[LocationSummary]:
    result = await db.execute(
        select(Location)
        .join(ProjectLocation, ProjectLocation.location_id == Location.id)
        .where(ProjectLocation.project_id == project_id)
        .order_by(Location.title, Location.id)
    )
    return [serialize_summary(location) for location in result.scalars().all()]


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    organization_id: OrganizationId,
    db: DbSession,
    project_status: Annotated[ProjectStatus | None, Query(alias="status")] = None,
) -> list[ProjectResponse]:
    counts = (
        select(
            ProjectLocation.project_id.label("project_id"),
            func.count(ProjectLocation.id).label("location_count"),
        )
        .group_by(ProjectLocation.project_id)
        .subquery()
    )
    statement = (
        select(Project, func.coalesce(counts.c.location_count, 0))
        .outerjoin(counts, counts.c.project_id == Project.id)
        .where(Project.organization_id == organization_id)
        .order_by(Project.created_at.desc(), Project.id)
    )
    if project_status is not None:
        statement = statement.where(Project.status == project_status)
    result = await db.execute(statement)
    return [serialize_project(project, count) for project, count in result.all()]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    organization_id: OrganizationId,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectResponse:
    if payload.google_connection_id is not None:
        owns_connection = await db.scalar(
            select(GoogleConnection.id).where(
                GoogleConnection.id == payload.google_connection_id,
                GoogleConnection.organization_id == organization_id,
            )
        )
        if owns_connection is None:
            raise HTTPException(status_code=400, detail="Google connection not found")

    location_ids = await owned_location_ids(db, organization_id, payload.location_ids or [])
    project = Project(
        organization_id=organization_id,
        name=payload.name,
        slug=await unique_slug(db, organization_id, payload.name),
        google_connection_id=payload.google_connection_id,
        created_by_user_id=current_user.id,
    )
    try:
        db.add(project)
        await db.flush()
        await link_locations(db, project.id, location_ids)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="A project with this name already exists"
        ) from None
    # A profile entering the product should not sit unaudited behind an empty screen.
    await enqueue_audits(db, organization_id, location_ids)
    return serialize_project(project, len(location_ids))


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: UUID, organization_id: OrganizationId, db: DbSession
) -> ProjectDetailResponse:
    project = await owned_project(db, organization_id, project_id)
    return serialize_detail(project, await project_locations(db, project.id))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID, payload: ProjectUpdate, organization_id: OrganizationId, db: DbSession
) -> ProjectResponse:
    project = await owned_project(db, organization_id, project_id)
    if payload.name is not None:
        project.name = payload.name
    if payload.status is not None:
        project.status = payload.status
    await db.commit()
    count = await db.scalar(
        select(func.count(ProjectLocation.id)).where(ProjectLocation.project_id == project.id)
    )
    return serialize_project(project, count or 0)


@router.post("/{project_id}/locations", response_model=ProjectDetailResponse)
async def add_project_locations(
    project_id: UUID,
    payload: ProjectLocationsRequest,
    organization_id: OrganizationId,
    db: DbSession,
) -> ProjectDetailResponse:
    project = await owned_project(db, organization_id, project_id)
    location_ids = await owned_location_ids(db, organization_id, payload.location_ids)
    await link_locations(db, project.id, location_ids)
    await db.commit()
    await enqueue_audits(db, organization_id, location_ids)
    return serialize_detail(project, await project_locations(db, project.id))


@router.delete("/{project_id}/locations/{location_id}", response_model=MessageResponse)
async def remove_project_location(
    project_id: UUID, location_id: UUID, organization_id: OrganizationId, db: DbSession
) -> MessageResponse:
    project = await owned_project(db, organization_id, project_id)
    result = await db.execute(
        delete(ProjectLocation).where(
            ProjectLocation.project_id == project.id,
            ProjectLocation.location_id == location_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Location is not in this project")
    await db.commit()
    return MessageResponse(message="Location removed from project")


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: UUID, organization_id: OrganizationId, db: DbSession
) -> MessageResponse:
    project = await owned_project(db, organization_id, project_id)
    # Only the project and its links go: the locations stay in the organization.
    await db.execute(delete(ProjectLocation).where(ProjectLocation.project_id == project.id))
    await db.execute(delete(Project).where(Project.id == project.id))
    await db.commit()
    return MessageResponse(message="Project deleted")
