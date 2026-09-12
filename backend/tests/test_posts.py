from datetime import date

from conftest import register_router, sign_in
from httpx import AsyncClient

from app.models import DataSource, Location, Post, PostCtaType, PostType

from app.api.posts import router as posts_router  # isort: skip

register_router(posts_router)


async def test_posts_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/posts")).status_code == 401


async def test_posts_are_scoped_filterable_and_paged(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    async with session_factory() as session:
        first = Location(
            organization_id=organization_id,
            google_location_name="locations/first",
            title="First clinic",
        )
        second = Location(
            organization_id=organization_id,
            google_location_name="locations/second",
            title="Second clinic",
        )
        session.add_all([first, second])
        await session.flush()
        session.add_all(
            [
                Post(
                    organization_id=organization_id,
                    location_id=first.id,
                    google_post_id="post-1",
                    post_type=PostType.offer,
                    summary="New patient offer",
                    cta_type=PostCtaType.get_offer,
                    published_on=date(2026, 9, 10),
                    source=DataSource.google,
                ),
                Post(
                    organization_id=organization_id,
                    location_id=second.id,
                    google_post_id="post-2",
                    post_type=PostType.standard,
                    summary="Opening update",
                    published_on=date(2026, 9, 11),
                    source=DataSource.google,
                ),
            ]
        )
        await session.commit()
        first_id = first.id

    response = await client.get("/api/v1/posts", headers=headers, params={"limit": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["location_title"] == "Second clinic"

    filtered = (
        await client.get(
            "/api/v1/posts",
            headers=headers,
            params={"location_id": str(first_id), "post_type": "offer"},
        )
    ).json()
    assert filtered["total"] == 1
    assert filtered["items"][0]["google_post_id"] == "post-1"
    assert filtered["items"][0]["cta_type"] == "get_offer"


async def test_posts_reject_unknown_location(client: AsyncClient) -> None:
    from uuid import uuid4

    headers, _ = await sign_in(client)
    response = await client.get(
        "/api/v1/posts", headers=headers, params={"location_id": str(uuid4())}
    )
    assert response.status_code == 404
