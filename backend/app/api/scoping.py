from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.models import OrganizationMembership


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
