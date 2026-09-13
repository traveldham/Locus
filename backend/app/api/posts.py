"""Published Google Business Profile posts across the organization."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import DbSession
from app.api.scoping import OrganizationId, project_locations
from app.models import DataSource, Location, Post, PostType
from app.schemas import PostListResponse, PostResponse

router = APIRouter(prefix="/posts", tags=["Posts"])
DEFAULT_LIMIT = 25
MAX_LIMIT = 200


@router.get("", response_model=PostListResponse)
async def list_posts(
    organization_id: OrganizationId,
    db: DbSession,
    location_id: UUID | None = None,
    project_id: UUID | None = None,
    post_type: PostType | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PostListResponse:
    conditions = [Post.organization_id == organization_id]
    if location_id is not None:
        owns = await db.scalar(
            select(Location.id).where(
                Location.id == location_id, Location.organization_id == organization_id
            )
        )
        if owns is None:
            raise HTTPException(status_code=404, detail="Location not found")
        conditions.append(Post.location_id == location_id)
    if project_id is not None:
        conditions.append(
            Post.location_id.in_(await project_locations(db, organization_id, project_id))
        )
    if post_type is not None:
        conditions.append(Post.post_type == post_type)

    total = await db.scalar(select(func.count()).select_from(Post).where(*conditions)) or 0
    rows = await db.execute(
        select(Post, Location.title)
        .join(Location, Location.id == Post.location_id)
        .where(*conditions)
        .order_by(Post.published_on.desc().nulls_last(), Post.id)
        .limit(limit)
        .offset(offset)
    )
    items = []
    for post, title in rows.all():
        item = PostResponse.model_validate(post)
        item.location_title = title
        items.append(item)
    return PostListResponse(
        items=items, total=total, limit=limit, offset=offset, source=DataSource.google
    )
