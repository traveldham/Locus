"""The organization's Google connection, as a read-only fact.

There is no OAuth flow left to run: Google never approved this project for Business
Profile API access, so the connection is written once by `app.seed` and only read back
here, which is what lets the UI show the integration as connected.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.models import GoogleConnection, OrganizationMembership, User
from app.schemas import ConnectionResponse

router = APIRouter(prefix="/integrations/google", tags=["Integrations"])


def serialize_connection(connection: GoogleConnection) -> ConnectionResponse:
    return ConnectionResponse(
        id=connection.id,
        google_account_email=connection.google_account_email,
        status=connection.status,
        scopes=connection.scopes.split() if connection.scopes else [],
        connected_at=connection.created_at,
        last_synced_at=connection.last_synced_at,
    )


async def current_organization_id(db: DbSession, user: User) -> UUID:
    organization_id = await db.scalar(
        select(OrganizationMembership.organization_id)
        .where(OrganizationMembership.user_id == user.id)
        .order_by(OrganizationMembership.created_at)
        .limit(1)
    )
    if organization_id is None:
        raise HTTPException(status_code=400, detail="User does not belong to an organization")
    return organization_id


async def find_connection(db: DbSession, organization_id: UUID) -> GoogleConnection | None:
    return await db.scalar(
        select(GoogleConnection)
        .where(GoogleConnection.organization_id == organization_id)
        .order_by(GoogleConnection.created_at.desc())
        .limit(1)
    )


async def ensure_connection(db: DbSession, organization_id: UUID) -> GoogleConnection:
    """The organization's Google connection, or a 409 saying the seed has not been run."""
    connection = await find_connection(db, organization_id)
    if connection is None:
        raise HTTPException(status_code=409, detail="Connect a Google account first")
    return connection


@router.get("", response_model=ConnectionResponse | None)
async def get_connection(current_user: CurrentUser, db: DbSession) -> ConnectionResponse | None:
    organization_id = await current_organization_id(db, current_user)
    connection = await find_connection(db, organization_id)
    return serialize_connection(connection) if connection else None
