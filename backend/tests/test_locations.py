from uuid import UUID, uuid4

from conftest import sign_in
from httpx import AsyncClient

from app.models import (
    AttributeCatalogItem,
    Location,
    LocationAttributeValue,
    LocationCategory,
    LocationHoursPeriod,
    OpenStatus,
)


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


async def seed_rich_location(session_factory, organization_id: UUID) -> str:
    async with session_factory() as session:
        location = Location(
            organization_id=organization_id,
            google_location_name="locations/9001",
            title="Bandra Clinic",
            store_code="BND-01",
            address_lines=["Shop 4", "  ", "Hill Road"],
            locality="Mumbai",
            administrative_area="Maharashtra",
            postal_code="400050",
            region_code="IN",
            open_status=OpenStatus.open,
            maps_uri="https://maps.google.com/?cid=9001",
            new_review_uri="https://search.google.com/local/writereview?placeid=9001",
        )
        session.add(location)
        await session.flush()
        session.add_all(
            [
                LocationCategory(
                    location_id=location.id,
                    category_name="categories/gcid:dentist",
                    display_name="Dentist",
                    is_primary=True,
                ),
                # Two periods on the same day plus an overnight span.
                LocationHoursPeriod(
                    location_id=location.id,
                    open_day="MONDAY",
                    open_hour=9,
                    close_day="MONDAY",
                    close_hour=13,
                ),
                LocationHoursPeriod(
                    location_id=location.id,
                    open_day="MONDAY",
                    open_hour=17,
                    close_day="TUESDAY",
                    close_hour=2,
                ),
                LocationAttributeValue(
                    location_id=location.id,
                    attribute_id="has_wheelchair_accessible_entrance",
                    value_type="BOOL",
                    values=[True],
                ),
                LocationAttributeValue(
                    location_id=location.id,
                    attribute_id="url_appointment",
                    value_type="URL",
                    values=["https://example.com/book"],
                ),
            ]
        )
        await session.commit()
        return str(location.id)


async def test_locations_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/locations")).status_code == 401
    assert (await client.get(f"/api/v1/locations/{uuid4()}")).status_code == 401
    assert (await client.get("/api/v1/locations/attribute-catalog")).status_code == 401


async def test_attribute_catalog_is_complete_and_organization_scoped(
    client: AsyncClient, session_factory
) -> None:
    headers, organization_id = await sign_in(client)
    async with session_factory() as session:
        session.add(
            AttributeCatalogItem(
                organization_id=organization_id,
                external_attribute_id="attr_01",
                attribute_name="wheelchair_accessible_entrance",
                attribute_group="accessibility",
                applies_to_category="Dentist",
                value_type="bool",
            )
        )
        await session.commit()

    body = (await client.get("/api/v1/locations/attribute-catalog", headers=headers)).json()
    assert body["total"] == 1
    assert body["items"] == [
        {
            "external_attribute_id": "attr_01",
            "attribute_name": "wheelchair_accessible_entrance",
            "attribute_group": "accessibility",
            "applies_to_category": "Dentist",
            "value_type": "bool",
        }
    ]


async def test_location_detail_shape(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    location_id = await seed_rich_location(session_factory, organization_id)

    response = await client.get(f"/api/v1/locations/{location_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["address"] == "Shop 4, Hill Road, Mumbai, Maharashtra, 400050"
    assert body["maps_uri"] == "https://maps.google.com/?cid=9001"
    assert body["new_review_uri"].startswith("https://search.google.com/local/writereview")
    assert body["categories"] == [
        {
            "category_name": "categories/gcid:dentist",
            "display_name": "Dentist",
            "is_primary": True,
        }
    ]
    # Periods are returned raw, never collapsed to one row per weekday.
    assert len(body["hours_periods"]) == 2
    assert {period["close_day"] for period in body["hours_periods"]} == {"MONDAY", "TUESDAY"}
    attributes = {item["attribute_id"]: item for item in body["attributes"]}
    assert attributes["has_wheelchair_accessible_entrance"]["values"] == [True]
    assert attributes["url_appointment"]["value_type"] == "URL"

    assert (await client.get(f"/api/v1/locations/{uuid4()}", headers=headers)).status_code == 404


async def test_location_listing_filters_and_search(client: AsyncClient, session_factory) -> None:
    headers, organization_id = await sign_in(client)
    bandra = await seed_location(
        session_factory, organization_id, "Bandra Clinic", store_code="BND-01", locality="Mumbai"
    )
    andheri = await seed_location(
        session_factory, organization_id, "Andheri Clinic", store_code="AND-02", locality="Mumbai"
    )
    indiranagar = await seed_location(
        session_factory,
        organization_id,
        "Indiranagar Clinic",
        store_code="IND-03",
        locality="Bengaluru",
    )

    everything = await client.get("/api/v1/locations", headers=headers)
    assert [item["title"] for item in everything.json()] == [
        "Andheri Clinic",
        "Bandra Clinic",
        "Indiranagar Clinic",
    ]

    project = (
        await client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "Mumbai Clinics", "location_ids": [bandra, andheri]},
        )
    ).json()
    filtered = await client.get(
        "/api/v1/locations", headers=headers, params={"project_id": project["id"]}
    )
    assert {item["id"] for item in filtered.json()} == {bandra, andheri}

    by_title = await client.get("/api/v1/locations", headers=headers, params={"q": "bandra"})
    assert [item["id"] for item in by_title.json()] == [bandra]

    by_store_code = await client.get("/api/v1/locations", headers=headers, params={"q": "IND-03"})
    assert [item["id"] for item in by_store_code.json()] == [indiranagar]

    by_locality = await client.get("/api/v1/locations", headers=headers, params={"q": "Bengaluru"})
    assert [item["id"] for item in by_locality.json()] == [indiranagar]

    wildcards_are_literal = await client.get(
        "/api/v1/locations", headers=headers, params={"q": "%"}
    )
    assert wildcards_are_literal.json() == []

    paged = await client.get("/api/v1/locations", headers=headers, params={"limit": 1, "offset": 1})
    assert [item["title"] for item in paged.json()] == ["Bandra Clinic"]

    over_cap = await client.get("/api/v1/locations", headers=headers, params={"limit": 5000})
    assert over_cap.status_code == 422


async def test_cross_organization_location_access_returns_404(
    client: AsyncClient, session_factory
) -> None:
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
    assert (await client.get("/api/v1/locations", headers=intruder)).json() == []
    assert (
        await client.get(f"/api/v1/locations/{location_id}", headers=intruder)
    ).status_code == 404
    assert (
        await client.get(
            "/api/v1/locations", headers=intruder, params={"project_id": project["id"]}
        )
    ).status_code == 404
