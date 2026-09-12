from uuid import UUID, uuid4

from conftest import sign_in
from httpx import AsyncClient

from app.models import Location


async def seed_location(session_factory, organization_id: UUID, title: str, **kwargs) -> str:
    async with session_factory() as session:
        location = Location(
            organization_id=organization_id,
            google_location_name=f"locations/{uuid4().hex[:12]}",
            title=title,
            **kwargs,
        )
        session.add(location)
        await session.commit()
        return str(location.id)


async def test_projects_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/projects")).status_code == 401
    assert (await client.post("/api/v1/projects", json={"name": "Clinics"})).status_code == 401
    assert (await client.get(f"/api/v1/projects/{uuid4()}")).status_code == 401


async def test_create_list_and_get_project(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    first = await seed_location(session_factory, organization_id, "Bandra Clinic")
    second = await seed_location(session_factory, organization_id, "Andheri Clinic")

    created = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "  Mumbai Clinics  ", "location_ids": [first, second]},
    )
    assert created.status_code == 201
    project = created.json()
    assert project["name"] == "Mumbai Clinics"
    assert project["slug"] == "mumbai-clinics"
    assert project["status"] == "active"
    assert project["location_count"] == 2

    listed = await client.get("/api/v1/projects", headers=headers)
    assert listed.status_code == 200
    assert [item["location_count"] for item in listed.json()] == [2]

    detail = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert detail.status_code == 200
    assert [item["title"] for item in detail.json()["locations"]] == [
        "Andheri Clinic",
        "Bandra Clinic",
    ]

    renamed = await client.patch(
        f"/api/v1/projects/{project['id']}",
        headers=headers,
        json={"name": "Mumbai Dental", "status": "archived"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Mumbai Dental"
    assert renamed.json()["status"] == "archived"
    assert renamed.json()["location_count"] == 2

    short_name = await client.post("/api/v1/projects", headers=headers, json={"name": " A "})
    assert short_name.status_code == 422

    unknown_location = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Ghost Project", "location_ids": [str(uuid4())]},
    )
    assert unknown_location.status_code == 400


async def test_slug_is_unique_within_the_organization(client: AsyncClient) -> None:
    headers, _ = await sign_in(client)

    slugs = []
    for _ in range(3):
        response = await client.post(
            "/api/v1/projects", headers=headers, json={"name": "Retail Stores"}
        )
        assert response.status_code == 201
        slugs.append(response.json()["slug"])
    assert slugs == ["retail-stores", "retail-stores-2", "retail-stores-3"]

    # A second organization may reuse the same slug: uniqueness is per-org.
    other_headers, _ = await sign_in(client, "other@example.com", "Southstar Retail")
    other = await client.post(
        "/api/v1/projects", headers=other_headers, json={"name": "Retail Stores"}
    )
    assert other.status_code == 201
    assert other.json()["slug"] == "retail-stores"


async def test_adding_locations_is_idempotent(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    location_id = await seed_location(session_factory, organization_id, "Bandra Clinic")
    project = (
        await client.post("/api/v1/projects", headers=headers, json={"name": "Mumbai Clinics"})
    ).json()

    for _ in range(2):
        added = await client.post(
            f"/api/v1/projects/{project['id']}/locations",
            headers=headers,
            json={"location_ids": [location_id, location_id]},
        )
        assert added.status_code == 200
        assert added.json()["location_count"] == 1


async def test_unlinking_and_deleting_keep_the_locations(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    first = await seed_location(session_factory, organization_id, "Bandra Clinic")
    second = await seed_location(session_factory, organization_id, "Andheri Clinic")
    project = (
        await client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "Mumbai Clinics", "location_ids": [first, second]},
        )
    ).json()
    other_project = (
        await client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "All Clinics", "location_ids": [first]},
        )
    ).json()

    unlinked = await client.delete(
        f"/api/v1/projects/{project['id']}/locations/{first}", headers=headers
    )
    assert unlinked.status_code == 200
    assert (await client.get(f"/api/v1/locations/{first}", headers=headers)).status_code == 200
    assert (await client.get(f"/api/v1/projects/{other_project['id']}", headers=headers)).json()[
        "location_count"
    ] == 1

    repeat_unlink = await client.delete(
        f"/api/v1/projects/{project['id']}/locations/{first}", headers=headers
    )
    assert repeat_unlink.status_code == 404

    deleted = await client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert deleted.status_code == 200
    gone = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert gone.status_code == 404

    surviving = await client.get("/api/v1/locations", headers=headers)
    assert {item["id"] for item in surviving.json()} == {first, second}


async def test_cross_organization_access_returns_404(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    location_id = await seed_location(session_factory, organization_id, "Bandra Clinic")
    project = (
        await client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "Mumbai Clinics", "location_ids": [location_id]},
        )
    ).json()

    intruder, _ = await sign_in(client, "intruder@example.com", "Rival Group")
    assert (await client.get("/api/v1/projects", headers=intruder)).json() == []
    assert (
        await client.get(f"/api/v1/projects/{project['id']}", headers=intruder)
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/v1/projects/{project['id']}", headers=intruder, json={"name": "Stolen"}
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/projects/{project['id']}/locations",
            headers=intruder,
            json={"location_ids": [location_id]},
        )
    ).status_code == 404
    assert (
        await client.delete(
            f"/api/v1/projects/{project['id']}/locations/{location_id}", headers=intruder
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/projects/{project['id']}", headers=intruder)
    ).status_code == 404

    # A foreign location cannot be smuggled into the intruder's own project either.
    borrowed = await client.post(
        "/api/v1/projects",
        headers=intruder,
        json={"name": "Borrowed", "location_ids": [location_id]},
    )
    assert borrowed.status_code == 400
    assert location_id in borrowed.json()["detail"]

    # The victim's project is untouched.
    assert (await client.get(f"/api/v1/projects/{project['id']}", headers=headers)).json()[
        "location_count"
    ] == 1
