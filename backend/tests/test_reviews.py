from uuid import UUID, uuid4

from conftest import sign_in
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models import ActionStatus, Location, ProfileAction, Review, SyncKind, SyncRun
from stubs import (
    HARBOUR_POINT,
    HARBOUR_POINT_REVIEW_COUNT,
    RIVERSIDE,
    RIVERSIDE_REPLIED_COUNT,
    RIVERSIDE_REVIEW_COUNT,
    STUB_ACCOUNT,
)

# The two locations the stub reviews provider knows about.
STUB_TOTAL_REVIEWS = RIVERSIDE_REVIEW_COUNT + HARBOUR_POINT_REVIEW_COUNT
ACCOUNT = STUB_ACCOUNT.resource_name


async def seed_location(
    session_factory,
    organization_id: UUID,
    title: str,
    google_location_name: str,
    *,
    account_qualified: bool = True,
) -> str:
    async with session_factory() as session:
        location = Location(
            organization_id=organization_id,
            google_location_name=google_location_name,
            # The v4 reviews API needs the account-qualified form, not locations/{id}.
            google_resource_name=(
                f"{ACCOUNT}/{google_location_name}" if account_qualified else None
            ),
            title=title,
        )
        session.add(location)
        await session.commit()
        return str(location.id)


async def test_reviews_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/reviews")).status_code == 401
    assert (await client.get(f"/api/v1/reviews/{uuid4()}")).status_code == 401
    assert (await client.post("/api/v1/reviews/sync")).status_code == 401
    assert (
        await client.put(f"/api/v1/reviews/{uuid4()}/reply", json={"comment": "Thanks!"})
    ).status_code == 401
    assert (await client.delete(f"/api/v1/reviews/{uuid4()}/reply")).status_code == 401


async def test_sync_imports_reviews_and_is_idempotent(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)

    first = await client.post("/api/v1/reviews/sync", headers=headers)
    assert first.status_code == 200
    body = first.json()
    assert body["locations_synced"] == 1
    assert body["created"] == RIVERSIDE_REVIEW_COUNT
    assert body["updated"] == 0
    assert body["skipped"] == []

    second = await client.post("/api/v1/reviews/sync", headers=headers)
    assert second.status_code == 200
    assert second.json()["created"] == 0
    assert second.json()["updated"] == RIVERSIDE_REVIEW_COUNT

    async with session_factory() as session:
        # Re-running updates in place via (location_id, google_review_id) — never duplicates.
        assert await session.scalar(select(func.count(Review.id))) == RIVERSIDE_REVIEW_COUNT
        runs = (
            (await session.execute(select(SyncRun).where(SyncRun.kind == SyncKind.reviews)))
            .scalars()
            .all()
        )
        assert len(runs) == 2
        assert all(run.records_written == RIVERSIDE_REVIEW_COUNT for run in runs)


async def test_sync_reports_locations_missing_the_v4_resource_name(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(
        session_factory, organization_id, "Riverside", RIVERSIDE, account_qualified=False
    )

    body = (await client.post("/api/v1/reviews/sync", headers=headers)).json()
    assert body["total"] == 0
    assert body["locations_synced"] == 0
    assert [item["location_id"] for item in body["skipped"]] == [location_id]
    assert "accounts/" in body["skipped"][0]["reason"]


async def test_sync_without_a_google_connection_asks_the_user_to_connect(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)

    response = await client.post("/api/v1/reviews/sync", headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Connect a Google account first"


async def test_inbox_filters_and_pagination(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    riverside = await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)
    harbour = await seed_location(session_factory, organization_id, "Harbour Point", HARBOUR_POINT)
    synced = (await client.post("/api/v1/reviews/sync", headers=headers)).json()
    assert synced["created"] == STUB_TOTAL_REVIEWS

    everything = (await client.get("/api/v1/reviews", headers=headers)).json()
    assert everything["total"] == STUB_TOTAL_REVIEWS
    assert everything["limit"] == 50
    assert len(everything["items"]) == STUB_TOTAL_REVIEWS
    # Newest first.
    create_times = [item["create_time"] for item in everything["items"]]
    assert create_times == sorted(create_times, reverse=True)
    assert everything["items"][0]["location_title"] in {"Riverside", "Harbour Point"}

    by_location = (
        await client.get("/api/v1/reviews", headers=headers, params={"location_id": riverside})
    ).json()
    assert by_location["total"] == RIVERSIDE_REVIEW_COUNT
    assert {item["location_id"] for item in by_location["items"]} == {riverside}

    project = (
        await client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "Harbourside", "location_ids": [harbour]},
        )
    ).json()
    by_project = (
        await client.get("/api/v1/reviews", headers=headers, params={"project_id": project["id"]})
    ).json()
    assert by_project["total"] == HARBOUR_POINT_REVIEW_COUNT
    assert {item["location_id"] for item in by_project["items"]} == {harbour}
    assert (
        await client.get("/api/v1/reviews", headers=headers, params={"project_id": str(uuid4())})
    ).status_code == 404

    by_rating = (
        await client.get(
            "/api/v1/reviews", headers=headers, params={"location_id": harbour, "rating": 1}
        )
    ).json()
    assert by_rating["total"] > 0
    assert {item["star_rating"] for item in by_rating["items"]} == {1}

    replied = (
        await client.get(
            "/api/v1/reviews", headers=headers, params={"location_id": riverside, "replied": True}
        )
    ).json()
    unreplied = (
        await client.get(
            "/api/v1/reviews", headers=headers, params={"location_id": riverside, "replied": False}
        )
    ).json()
    assert replied["total"] == RIVERSIDE_REPLIED_COUNT
    assert unreplied["total"] == RIVERSIDE_REVIEW_COUNT - RIVERSIDE_REPLIED_COUNT
    assert all(item["has_reply"] for item in replied["items"])
    assert all(item["reply_comment"] is None for item in unreplied["items"])

    paged = (
        await client.get("/api/v1/reviews", headers=headers, params={"limit": 3, "offset": 2})
    ).json()
    assert paged["offset"] == 2
    assert [item["id"] for item in paged["items"]] == [
        item["id"] for item in everything["items"][2:5]
    ]

    assert (
        await client.get("/api/v1/reviews", headers=headers, params={"limit": 5000})
    ).status_code == 422
    assert (
        await client.get("/api/v1/reviews", headers=headers, params={"rating": 9})
    ).status_code == 422


async def test_search_filters_by_text(client: AsyncClient, session_factory, connect_google) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)
    await client.post("/api/v1/reviews/sync", headers=headers)

    hits = (await client.get("/api/v1/reviews", headers=headers, params={"q": "parking"})).json()
    assert hits["total"] == 2
    assert all("parking" in (item["comment"] or "").lower() for item in hits["items"])

    assert (await client.get("/api/v1/reviews", headers=headers, params={"q": "%"})).json()[
        "total"
    ] == 0


async def test_reply_is_audited_then_removed(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)
    await client.post("/api/v1/reviews/sync", headers=headers)

    target = (
        await client.get("/api/v1/reviews", headers=headers, params={"replied": False, "limit": 1})
    ).json()["items"][0]
    assert target["has_reply"] is False

    reply = await client.put(
        f"/api/v1/reviews/{target['id']}/reply",
        headers=headers,
        json={"comment": "  Thank you for the kind words!  "},
    )
    assert reply.status_code == 200
    body = reply.json()
    assert body["reply_comment"] == "Thank you for the kind words!"
    assert body["has_reply"] is True
    assert body["reply_update_time"] is not None

    async with session_factory() as session:
        actions = (await session.execute(select(ProfileAction))).scalars().all()
        assert [action.action_type for action in actions] == ["reply_to_review"]
        assert actions[0].status == ActionStatus.succeeded
        assert actions[0].payload["comment"] == "Thank you for the kind words!"
        assert actions[0].location_id is not None

    # The reply survives a re-sync: the provider now reports it as the review's reply.
    await client.post("/api/v1/reviews/sync", headers=headers)
    assert (await client.get(f"/api/v1/reviews/{target['id']}", headers=headers)).json()[
        "reply_comment"
    ] == "Thank you for the kind words!"

    removed = await client.delete(f"/api/v1/reviews/{target['id']}/reply", headers=headers)
    assert removed.status_code == 200
    assert removed.json()["reply_comment"] is None
    assert removed.json()["has_reply"] is False

    async with session_factory() as session:
        actions = (
            (
                await session.execute(
                    select(ProfileAction).where(ProfileAction.action_type == "delete_review_reply")
                )
            )
            .scalars()
            .all()
        )
        assert [action.status for action in actions] == [ActionStatus.succeeded]

    # Nothing left to remove.
    assert (
        await client.delete(f"/api/v1/reviews/{target['id']}/reply", headers=headers)
    ).status_code == 404


async def test_reply_rejects_empty_and_oversized_text(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)
    await client.post("/api/v1/reviews/sync", headers=headers)
    review_id = (await client.get("/api/v1/reviews", headers=headers, params={"limit": 1})).json()[
        "items"
    ][0]["id"]

    for comment in ("", "   ", "x" * 4097):
        response = await client.put(
            f"/api/v1/reviews/{review_id}/reply", headers=headers, json={"comment": comment}
        )
        assert response.status_code == 422, comment


async def test_there_is_no_endpoint_for_deleting_a_customer_review(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)
    await client.post("/api/v1/reviews/sync", headers=headers)
    review_id = (await client.get("/api/v1/reviews", headers=headers, params={"limit": 1})).json()[
        "items"
    ][0]["id"]

    # A business can remove its own reply, never the customer's review.
    assert (await client.delete(f"/api/v1/reviews/{review_id}", headers=headers)).status_code == 405


async def test_cross_organization_access_returns_404(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id, "Riverside", RIVERSIDE)
    await client.post("/api/v1/reviews/sync", headers=headers)
    review_id = (await client.get("/api/v1/reviews", headers=headers, params={"limit": 1})).json()[
        "items"
    ][0]["id"]

    intruder, _ = await sign_in(client, "intruder@example.com", "Rival Group")
    assert (await client.get("/api/v1/reviews", headers=intruder)).json()["total"] == 0
    assert (await client.get(f"/api/v1/reviews/{review_id}", headers=intruder)).status_code == 404
    assert (
        await client.get("/api/v1/reviews", headers=intruder, params={"location_id": location_id})
    ).status_code == 404
    assert (
        await client.put(
            f"/api/v1/reviews/{review_id}/reply", headers=intruder, json={"comment": "Hello"}
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/reviews/{review_id}/reply", headers=intruder)
    ).status_code == 404
    assert (
        await client.post(
            "/api/v1/reviews/sync", headers=intruder, params={"location_id": location_id}
        )
    ).status_code == 404
