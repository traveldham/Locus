from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.models import OrganizationMembership, Project, ProjectLocation


async def get_organization_id(current_user: CurrentUser, db: DbSession) -> UUID:
    """Every tenant-scoped query hangs off this: the caller's first membership."""
    organization_id = await db.scalar(
        select(OrganizationMembership.organization_id)
        .where(OrganizationMembership.user_id == current_user.id)
        .order_by(OrganizationMembership.created_at, OrganizationMembership.id)
        .limit(1)
    )
    if organization_id is None:
        raise HTTPException(status_code=400, detail="User does not belong to an organization")
    return organization_id


OrganizationId = Annotated[UUID, Depends(get_organization_id)]


async def project_locations(db, organization_id: UUID, project_id: UUID):
    """A subquery of the locations in one project, for `location_id.in_(...)` filters.

    Validated against the organization first, so a project id from another tenant is a
    not-found rather than a silent cross-tenant read.
    """
    owns = await db.scalar(
        select(Project.id).where(
            Project.id == project_id, Project.organization_id == organization_id
        )
    )
    if owns is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return select(ProjectLocation.location_id).where(ProjectLocation.project_id == project_id)
