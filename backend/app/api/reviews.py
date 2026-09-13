"""The review inbox: every review across every location, and the owner's replies.

Reads come from our database — Google's per-minute quota could not survive a page load
per location — and `POST /reviews/sync` is what refills it. Writes (replying, removing a
reply) go straight to Google through the reviews provider and are only mirrored locally
once Google confirms, because a reply appears publicly on the business profile.

There is deliberately no endpoint for deleting a review: a business cannot delete what a
customer wrote, only its own reply.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import Select, func, or_, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.integrations import ensure_connection
from app.api.scoping import OrganizationId
from app.models import (
    ActionStatus,
    GoogleConnection,
    Location,
    ProfileAction,
    Project,
    ProjectLocation,
    Review,
    SyncKind,
    SyncRun,
    SyncStatus,
    utcnow,
)
from app.schemas import (
    ReviewListResponse,
    ReviewReplyRequest,
    ReviewResponse,
    ReviewSyncResponse,
)
from app.schemas.reviews import MAX_REPLY_LENGTH
from app.services.providers import ProviderError
from app.services.providers.reviews import ProviderReview, get_reviews_provider

router = APIRouter(prefix="/reviews", tags=["Reviews"])

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
REPLY_ACTION = "reply_to_review"
DELETE_REPLY_ACTION = "delete_review_reply"

# The v4 reviews API addresses a location as accounts/{a}/locations/{l}; without that
# name a location's reviews are unreachable, which the sync response reports per location
# instead of quietly returning an empty inbox.
MISSING_RESOURCE_NAME = (
    "No account-qualified Google resource name (accounts/{account}/locations/{location}); "
    "re-import this location to fetch its reviews."
)


def provider_failure(exc: Exception) -> HTTPException:
    """A provider problem is an upstream failure, never our 500."""
    return HTTPException(status_code=502, detail=str(exc))


def serialize(review: Review, location_title: str | None) -> ReviewResponse:
    item = ReviewResponse.model_validate(review)
    item.location_title = location_title
    item.has_reply = review.reply_comment is not None
    return item


def search_filter(statement: Select, term: str) -> Select:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return statement.where(
        or_(
            Review.comment.ilike(pattern, escape="\\"),
            Review.reviewer_display_name.ilike(pattern, escape="\\"),
            Review.reply_comment.ilike(pattern, escape="\\"),
        )
    )


async def owned_location(db: DbSession, organization_id: UUID, location_id: UUID) -> Location:
    location = await db.scalar(
        select(Location).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


async def owned_review(db: DbSession, organization_id: UUID, review_id: UUID) -> Review:
    review = await db.scalar(
        select(Review).where(Review.id == review_id, Review.organization_id == organization_id)
    )
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


async def location_title(db: DbSession, location_id: UUID) -> str | None:
    return await db.scalar(select(Location.title).where(Location.id == location_id))


async def reviews_connection(db: DbSession, organization_id: UUID) -> GoogleConnection:
    """The Google connection the reviews calls run as.

    Shared with the integrations router on purpose: two different answers to "which
    Google account are we acting as" would be a bug.
    """
    return await ensure_connection(db, organization_id)


def apply_review(review: Review, payload: ProviderReview) -> None:
    review.google_review_name = payload.google_review_name
    review.reviewer_display_name = payload.reviewer_display_name
    review.reviewer_photo_url = payload.reviewer_photo_url
    review.is_anonymous = payload.is_anonymous
    review.star_rating = payload.star_rating
    review.comment = payload.comment
    review.create_time = payload.create_time
    review.update_time = payload.update_time
    review.reply_comment = payload.reply_comment
    review.reply_update_time = payload.reply_update_time


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    organization_id: OrganizationId,
    db: DbSession,
    project_id: UUID | None = None,
    location_id: UUID | None = None,
    rating: Annotated[int | None, Query(ge=1, le=5)] = None,
    replied: bool | None = None,
    q: Annotated[str | None, Query(max_length=160)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReviewListResponse:
    statement = select(Review).where(Review.organization_id == organization_id)

    if project_id is not None:
        owns_project = await db.scalar(
            select(Project.id).where(
                Project.id == project_id, Project.organization_id == organization_id
            )
        )
        if owns_project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        statement = statement.join(
            ProjectLocation, ProjectLocation.location_id == Review.location_id
        ).where(ProjectLocation.project_id == project_id)

    if location_id is not None:
        await owned_location(db, organization_id, location_id)
        statement = statement.where(Review.location_id == location_id)

    if rating is not None:
        statement = statement.where(Review.star_rating == rating)

    if replied is not None:
        statement = statement.where(
            Review.reply_comment.is_not(None) if replied else Review.reply_comment.is_(None)
        )

    term = (q or "").strip()
    if term:
        statement = search_filter(statement, term)

    total = await db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    result = await db.execute(
        statement.add_columns(Location.title)
        .join(Location, Location.id == Review.location_id)
        # Newest first is what an inbox means; the id keeps paging stable on ties.
        .order_by(Review.create_time.desc(), Review.id)
        .limit(limit)
        .offset(offset)
    )
    return ReviewListResponse(
        items=[serialize(review, title) for review, title in result.all()],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/summary")
async def review_summary(location_id: UUID, organization_id: OrganizationId, db: DbSession):
    """Aggregate the entire stored review collection, never just a visible page."""
    await owned_location(db, organization_id, location_id)
    rows = (
        await db.execute(
            select(Review.star_rating, func.count(Review.id))
            .where(
                Review.organization_id == organization_id,
                Review.location_id == location_id,
                Review.star_rating.between(1, 5),
            )
            .group_by(Review.star_rating)
        )
    ).all()
    distribution = {str(rating): count for rating, count in rows}
    total = sum(distribution.values())
    return {
        "total": total,
        "average": round(
            sum(int(rating) * count for rating, count in distribution.items()) / total, 2
        )
        if total
        else None,
        "distribution": {str(rating): distribution.get(str(rating), 0) for rating in range(1, 6)},
    }


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID, organization_id: OrganizationId, db: DbSession
) -> ReviewResponse:
    review = await owned_review(db, organization_id, review_id)
    return serialize(review, await location_title(db, review.location_id))


@router.put("/{review_id}/reply", response_model=ReviewResponse)
async def reply_to_review(
    review_id: UUID,
    payload: ReviewReplyRequest,
    organization_id: OrganizationId,
    current_user: CurrentUser,
    db: DbSession,
) -> ReviewResponse:
    comment = payload.comment.strip()
    if not comment:
        raise HTTPException(status_code=422, detail="A reply cannot be empty")
    if len(comment) > MAX_REPLY_LENGTH:
        raise HTTPException(
            status_code=422, detail=f"A reply cannot exceed {MAX_REPLY_LENGTH} characters"
        )

    review = await owned_review(db, organization_id, review_id)
    location = await owned_location(db, organization_id, review.location_id)
    provider = get_reviews_provider()
    connection = await reviews_connection(db, organization_id)

    # The reply is published on a live public profile, so it is audited before it is sent
    # and the local copy is only updated once Google has confirmed the write.
    action = ProfileAction(
        organization_id=organization_id,
        location_id=location.id,
        user_id=current_user.id,
        action_type=REPLY_ACTION,
        payload={
            "review_id": str(review.id),
            "google_review_id": review.google_review_id,
            "comment": comment,
        },
        status=ActionStatus.pending,
    )
    db.add(action)
    await db.commit()

    action.status = ActionStatus.executing
    await db.commit()

    try:
        result = await provider.reply(connection, location, review.google_review_id, comment)
    except ProviderError as exc:
        action.status = ActionStatus.failed
        action.error = str(exc)
        await db.commit()
        raise provider_failure(exc) from exc

    review.reply_comment = result.reply_comment or comment
    review.reply_update_time = result.reply_update_time or utcnow()
    action.status = ActionStatus.succeeded
    action.google_response = {
        "google_review_id": result.google_review_id,
        "reply_update_time": (
            review.reply_update_time.isoformat() if review.reply_update_time else None
        ),
    }
    await db.commit()
    return serialize(review, location.title)


@router.delete("/{review_id}/reply", response_model=ReviewResponse)
async def delete_review_reply(
    review_id: UUID,
    organization_id: OrganizationId,
    current_user: CurrentUser,
    db: DbSession,
) -> ReviewResponse:
    review = await owned_review(db, organization_id, review_id)
    if review.reply_comment is None:
        raise HTTPException(status_code=404, detail="This review has no reply to remove")

    location = await owned_location(db, organization_id, review.location_id)
    provider = get_reviews_provider()
    connection = await reviews_connection(db, organization_id)

    action = ProfileAction(
        organization_id=organization_id,
        location_id=location.id,
        user_id=current_user.id,
        action_type=DELETE_REPLY_ACTION,
        payload={"review_id": str(review.id), "google_review_id": review.google_review_id},
        status=ActionStatus.pending,
    )
    db.add(action)
    await db.commit()

    action.status = ActionStatus.executing
    await db.commit()

    try:
        await provider.delete_reply(connection, location, review.google_review_id)
    except ProviderError as exc:
        action.status = ActionStatus.failed
        action.error = str(exc)
        await db.commit()
        raise provider_failure(exc) from exc

    review.reply_comment = None
    review.reply_update_time = None
    action.status = ActionStatus.succeeded
    await db.commit()
    return serialize(review, location.title)


@router.post("/sync", response_model=ReviewSyncResponse)
async def sync_reviews(
    organization_id: OrganizationId,
    current_user: CurrentUser,
    db: DbSession,
    location_id: UUID | None = None,
) -> ReviewSyncResponse:
    """Pull reviews from the provider and upsert them.

    Idempotent by construction: every row is matched on (location_id, google_review_id),
    the pair the unique constraint covers, so a second run refreshes instead of duplicating.
    """
    if location_id is not None:
        locations = [await owned_location(db, organization_id, location_id)]
    else:
        result = await db.execute(
            select(Location)
            .where(Location.organization_id == organization_id)
            .order_by(Location.title, Location.id)
        )
        locations = list(result.scalars().all())

    provider = get_reviews_provider()
    connection = await reviews_connection(db, organization_id)

    run = SyncRun(
        organization_id=organization_id,
        connection_id=connection.id,
        kind=SyncKind.reviews,
        status=SyncStatus.running,
        started_at=utcnow(),
    )
    db.add(run)
    await db.commit()

    created = updated = 0
    skipped: list[dict[str, str]] = []
    synced_locations = 0

    for location in locations:
        if not (location.google_resource_name or "").strip():
            skipped.append({"location_id": str(location.id), "reason": MISSING_RESOURCE_NAME})
            continue
        try:
            fetched = await provider.list_reviews(connection, location)
        except ProviderError as exc:
            run.status = SyncStatus.failed
            run.error = str(exc)
            run.finished_at = utcnow()
            run.records_written = created + updated
            await db.commit()
            raise provider_failure(exc) from exc

        existing_rows = await db.execute(select(Review).where(Review.location_id == location.id))
        existing = {row.google_review_id: row for row in existing_rows.scalars()}

        for payload in fetched:
            review = existing.get(payload.google_review_id)
            if review is None:
                review = Review(
                    organization_id=organization_id,
                    location_id=location.id,
                    google_review_id=payload.google_review_id,
                )
                db.add(review)
                existing[payload.google_review_id] = review
                created += 1
            else:
                updated += 1
            apply_review(review, payload)
        synced_locations += 1
        await db.flush()

    run.status = SyncStatus.succeeded
    run.records_written = created + updated
    run.finished_at = utcnow()
    await db.commit()

    return ReviewSyncResponse(
        sync_run_id=run.id,
        locations_synced=synced_locations,
        created=created,
        updated=updated,
        total=created + updated,
        skipped=skipped,
    )
