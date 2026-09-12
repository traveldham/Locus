from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.api.scoping import OrganizationId
from app.models import (
    ActionStatus,
    GoogleConnection,
    Location,
    ProfileAction,
    Project,
    ProjectLocation,
    User,
)
from app.schemas import (
    ActionUser,
    EditPreviewResponse,
    LocationDetail,
    LocationEditRequest,
    LocationSummary,
    ProfileActionResponse,
)
from app.services.location_edits import EditPlan, apply_locally, plan_edit
from app.services.providers import ProviderError, UpdateResult, get_provider

router = APIRouter(prefix="/locations", tags=["Locations"])

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
ACTION_TYPE = "location_update"
NO_CHANGES_DETAIL = "Nothing to update — the submitted values match the current profile."


def build_address(location: Location) -> str | None:
    """A readable single-line address, skipping the parts Google left empty."""
    parts = [
        *(location.address_lines or []),
        location.locality,
        location.administrative_area,
        location.postal_code,
    ]
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return ", ".join(cleaned) or None


def serialize_summary(location: Location) -> LocationSummary:
    summary = LocationSummary.model_validate(location)
    summary.address = build_address(location)
    return summary


def serialize_detail(location: Location) -> LocationDetail:
    detail = LocationDetail.model_validate(location)
    detail.address = build_address(location)
    return detail


def search_filter(statement: Select, term: str) -> Select:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return statement.where(
        or_(
            Location.title.ilike(pattern, escape="\\"),
            Location.store_code.ilike(pattern, escape="\\"),
            Location.locality.ilike(pattern, escape="\\"),
        )
    )


async def owned_location(db: DbSession, organization_id: UUID, location_id: UUID) -> Location:
    location = await db.scalar(
        select(Location)
        .options(
            selectinload(Location.categories),
            selectinload(Location.hours_periods),
            selectinload(Location.attributes),
        )
        .where(Location.id == location_id, Location.organization_id == organization_id)
    )
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.get("", response_model=list[LocationSummary])
async def list_locations(
    organization_id: OrganizationId,
    db: DbSession,
    project_id: UUID | None = None,
    q: Annotated[str | None, Query(max_length=160)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LocationSummary]:
    statement = select(Location).where(Location.organization_id == organization_id)

    if project_id is not None:
        owns_project = await db.scalar(
            select(Project.id).where(
                Project.id == project_id, Project.organization_id == organization_id
            )
        )
        if owns_project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        statement = statement.join(
            ProjectLocation, ProjectLocation.location_id == Location.id
        ).where(ProjectLocation.project_id == project_id)

    term = (q or "").strip()
    if term:
        statement = search_filter(statement, term)

    result = await db.execute(
        statement.order_by(Location.title, Location.id).limit(limit).offset(offset)
    )
    return [serialize_summary(location) for location in result.scalars().all()]


@router.get("/{location_id}", response_model=LocationDetail)
async def get_location(
    location_id: UUID, organization_id: OrganizationId, db: DbSession
) -> LocationDetail:
    return serialize_detail(await owned_location(db, organization_id, location_id))


# ---------------------------------------------------------------------------
# Editing a profile: preview -> confirm -> apply -> audit
#
# Google's API policy forbids changing a merchant's live profile without their express
# consent, so a write is always two requests. The first is a dry run (`validateOnly=true`)
# that returns the exact diff and any field errors; only a second, explicit call commits it.
# Every committed attempt leaves a `ProfileAction` behind whether it succeeds or not.
# ---------------------------------------------------------------------------


async def edit_connection(
    db: DbSession, organization_id: UUID, location: Location
) -> GoogleConnection:
    """The Google grant a write for this location goes out under."""
    connection = None
    if location.connection_id is not None:
        connection = await db.get(GoogleConnection, location.connection_id)
    if connection is None:
        connection = await db.scalar(
            select(GoogleConnection)
            .where(GoogleConnection.organization_id == organization_id)
            .order_by(GoogleConnection.created_at.desc())
            .limit(1)
        )
    if connection is None:
        raise HTTPException(status_code=409, detail="Connect a Google account first")
    return connection


def upstream_failure(exc: Exception) -> HTTPException:
    """A provider that could not serve the request is an upstream problem, never our 500."""
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


def serialize_action(action: ProfileAction, user: User | None) -> ProfileActionResponse:
    return ProfileActionResponse(
        id=action.id,
        action_type=action.action_type,
        status=action.status,
        payload=action.payload,
        error=action.error,
        created_at=action.created_at,
        user=ActionUser.model_validate(user) if user is not None else None,
    )


def action_payload(plan: EditPlan) -> dict[str, object]:
    return {
        "update_mask": plan.mask,
        "changes": [change.model_dump(mode="json") for change in plan.field_changes],
    }


async def record_failure(
    db: DbSession, action: ProfileAction, message: str, result: UpdateResult | None
) -> None:
    action.status = ActionStatus.failed
    action.error = message
    if result is not None:
        action.google_response = {
            "response": result.response,
            "field_errors": result.field_errors,
        }
    await db.commit()


@router.post("/{location_id}/edits/preview", response_model=EditPreviewResponse)
async def preview_edit(
    location_id: UUID,
    payload: LocationEditRequest,
    organization_id: OrganizationId,
    db: DbSession,
) -> EditPreviewResponse:
    """Dry run. Nothing is committed at Google and no audit row is written."""
    location = await owned_location(db, organization_id, location_id)
    plan = plan_edit(location, payload)
    if plan.is_empty:
        # An empty patch is never sent: Google would reject it, and there is nothing to show.
        return EditPreviewResponse(changes=[], update_mask=[], field_errors={}, valid=False)

    provider = get_provider()
    connection = await edit_connection(db, organization_id, location)
    try:
        result = await provider.update_location(
            connection, location, plan.changes, validate_only=True
        )
    except ProviderError as exc:
        raise upstream_failure(exc) from exc

    return EditPreviewResponse(
        changes=plan.field_changes,
        update_mask=plan.mask,
        field_errors=result.field_errors,
        valid=result.ok,
    )


@router.post(
    "/{location_id}/edits",
    response_model=ProfileActionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_edit(
    location_id: UUID,
    payload: LocationEditRequest,
    organization_id: OrganizationId,
    current_user: CurrentUser,
    db: DbSession,
) -> ProfileActionResponse:
    """Commit the edit the user confirmed, and record the attempt either way."""
    location = await owned_location(db, organization_id, location_id)
    plan = plan_edit(location, payload)
    if plan.is_empty:
        raise HTTPException(status_code=422, detail=NO_CHANGES_DETAIL)

    provider = get_provider()
    connection = await edit_connection(db, organization_id, location)

    # Written and committed before the request leaves: if this process dies mid-call the
    # audit trail still shows that an edit was attempted, and by whom.
    action = ProfileAction(
        organization_id=organization_id,
        location_id=location.id,
        user_id=current_user.id,
        action_type=ACTION_TYPE,
        payload=action_payload(plan),
        status=ActionStatus.pending,
    )
    db.add(action)
    await db.commit()

    action.status = ActionStatus.executing
    await db.commit()

    try:
        result = await provider.update_location(
            connection, location, plan.changes, validate_only=False
        )
    except ProviderError as exc:
        await record_failure(db, action, str(exc), None)
        raise upstream_failure(exc) from exc

    if not result.ok:
        message = result.error or "Google rejected the update"
        await record_failure(db, action, message, result)
        if result.field_errors:
            # The profile was rejected on its contents, which is the caller's input problem.
            raise HTTPException(
                status_code=422, detail={"message": message, "field_errors": result.field_errors}
            )
        raise HTTPException(status_code=502, detail=message)

    # Only now, with Google's confirmation in hand, does our copy move.
    await apply_locally(db, location, plan.changes)
    action.status = ActionStatus.succeeded
    action.google_response = {"response": result.response, "field_errors": {}}
    await db.commit()
    return serialize_action(action, current_user)


@router.get("/{location_id}/actions", response_model=list[ProfileActionResponse])
async def list_location_actions(
    location_id: UUID,
    organization_id: OrganizationId,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProfileActionResponse]:
    """Audit history for one location, newest first."""
    owns_location = await db.scalar(
        select(Location.id).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if owns_location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    result = await db.execute(
        select(ProfileAction, User)
        .outerjoin(User, User.id == ProfileAction.user_id)
        .where(
            ProfileAction.organization_id == organization_id,
            ProfileAction.location_id == location_id,
        )
        .order_by(ProfileAction.created_at.desc(), ProfileAction.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [serialize_action(action, user) for action, user in result.all()]
