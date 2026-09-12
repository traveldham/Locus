from uuid import UUID, uuid4

from conftest import sign_in
from httpx import AsyncClient
from sqlalchemy import select

from app.models import (
    Location,
    LocationAttributeValue,
    LocationCategory,
    LocationHoursPeriod,
    OpenStatus,
    ProfileAction,
)
from app.services.providers.base import (
    LocationChanges,
    ProviderAttribute,
    ProviderCategory,
    ProviderHoursPeriod,
    UpdateResult,
    build_update_mask,
)


async def seed_location(session_factory, organization_id: UUID) -> str:
    """A fully populated location, so "did an untouched field move?" is answerable."""
    async with session_factory() as session:
        location = Location(
            organization_id=organization_id,
            google_location_name="locations/9001",
            title="Bandra Clinic",
            store_code="BND-01",
            primary_category_name="categories/gcid:dentist",
            primary_category_display="Dentist",
            address_lines=["Hill Road"],
            locality="Mumbai",
            phone_primary="+91 22 5550 0101",
            website_uri="https://bandra.example.com",
            description="A dental clinic in Bandra.",
            open_status=OpenStatus.open,
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
                LocationHoursPeriod(
                    location_id=location.id,
                    open_day="MONDAY",
                    open_hour=9,
                    close_day="MONDAY",
                    close_hour=17,
                ),
                LocationAttributeValue(
                    location_id=location.id,
                    attribute_id="has_wheelchair_accessible_entrance",
                    value_type="BOOL",
                    values=[True],
                ),
            ]
        )
        await session.commit()
        return str(location.id)


async def read_location(session_factory, location_id: str) -> Location:
    async with session_factory() as session:
        return await session.get(Location, UUID(location_id))


async def read_actions(session_factory, location_id: str) -> list[ProfileAction]:
    async with session_factory() as session:
        result = await session.execute(
            select(ProfileAction)
            .where(ProfileAction.location_id == UUID(location_id))
            .order_by(ProfileAction.created_at)
        )
        return list(result.scalars())


class FailingProvider:
    """Stands in for a Google call that fails upstream rather than on its contents."""

    name = "stub"

    def __init__(self, result: UpdateResult) -> None:
        self.result = result
        self.calls: list[bool] = []

    async def update_location(self, connection, location, changes, *, validate_only):
        del connection, location
        self.calls.append(validate_only)
        return UpdateResult(
            ok=self.result.ok,
            field_errors=self.result.field_errors,
            applied_mask=build_update_mask(changes),
            response=self.result.response,
            error=self.result.error,
        )


async def test_edit_endpoints_require_authentication(client: AsyncClient) -> None:
    location_id = uuid4()
    assert (
        await client.post(f"/api/v1/locations/{location_id}/edits/preview", json={})
    ).status_code == 401
    assert (await client.post(f"/api/v1/locations/{location_id}/edits", json={})).status_code == 401
    assert (await client.get(f"/api/v1/locations/{location_id}/actions")).status_code == 401


async def test_preview_masks_only_genuinely_changed_fields(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)

    response = await client.post(
        f"/api/v1/locations/{location_id}/edits/preview",
        headers=headers,
        json={
            "title": "Bandra Dental Studio",
            # Resubmitted unchanged — these must not reach the mask.
            "phone_primary": "+91 22 5550 0101",
            "website_uri": "  https://bandra.example.com  ",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["update_mask"] == ["title"]
    assert body["valid"] is True
    assert body["field_errors"] == {}
    assert [change["field"] for change in body["changes"]] == ["title"]
    assert body["changes"][0] == {
        "field": "title",
        "label": "Business name",
        "current": "Bandra Clinic",
        "proposed": "Bandra Dental Studio",
    }
    # A preview is a dry run: no audit row, and the stored profile is untouched.
    assert await read_actions(session_factory, location_id) == []
    assert (await read_location(session_factory, location_id)).title == "Bandra Clinic"


async def test_preview_without_changes_is_empty_and_apply_is_rejected(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)
    identical = {
        "title": "Bandra Clinic",
        "phone_primary": "+91 22 5550 0101",
        "description": "A dental clinic in Bandra.",
        "open_status": "open",
        "hours_periods": [
            {"open_day": "MONDAY", "open_hour": 9, "close_day": "MONDAY", "close_hour": 17}
        ],
        "attributes": [
            {
                "attribute_id": "has_wheelchair_accessible_entrance",
                "value_type": "BOOL",
                "values": [True],
            }
        ],
        "primary_category": {"category_name": "categories/gcid:dentist"},
    }

    preview = await client.post(
        f"/api/v1/locations/{location_id}/edits/preview", headers=headers, json=identical
    )
    assert preview.status_code == 200
    assert preview.json()["update_mask"] == []
    assert preview.json()["changes"] == []
    assert preview.json()["valid"] is False

    # An empty patch is never sent to Google.
    applied = await client.post(
        f"/api/v1/locations/{location_id}/edits", headers=headers, json=identical
    )
    assert applied.status_code == 422
    assert await read_actions(session_factory, location_id) == []


async def test_untouched_fields_never_enter_the_update_mask(
    client: AsyncClient, session_factory, connect_google
) -> None:
    """The data-loss guard: an omitted field must not be listed, or Google unsets it."""
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)

    preview = await client.post(
        f"/api/v1/locations/{location_id}/edits/preview",
        headers=headers,
        json={"description": "Now open on Saturdays."},
    )
    assert preview.json()["update_mask"] == ["profile"]

    applied = await client.post(
        f"/api/v1/locations/{location_id}/edits",
        headers=headers,
        json={"description": "Now open on Saturdays."},
    )
    assert applied.status_code == 201
    assert applied.json()["payload"]["update_mask"] == ["profile"]

    location = await read_location(session_factory, location_id)
    assert location.description == "Now open on Saturdays."
    # Everything the request did not mention is exactly as it was.
    assert location.title == "Bandra Clinic"
    assert location.phone_primary == "+91 22 5550 0101"
    assert location.website_uri == "https://bandra.example.com"
    assert location.primary_category_name == "categories/gcid:dentist"
    assert location.open_status == OpenStatus.open


async def test_invalid_input_surfaces_field_errors_and_does_not_apply(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)
    invalid = {
        "title": "   ",
        "website_uri": "bandra-dental",
        "phone_primary": "call us!",
        "hours_periods": [
            {"open_day": "MONDAY", "open_hour": 18, "close_day": "MONDAY", "close_hour": 9}
        ],
    }

    preview = await client.post(
        f"/api/v1/locations/{location_id}/edits/preview", headers=headers, json=invalid
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["valid"] is False
    assert set(body["field_errors"]) == {
        "title",
        "website_uri",
        "phone_primary",
        "hours_periods",
    }
    # The diff is still reported, so the user sees what they tried to do.
    assert body["update_mask"] == ["title", "phoneNumbers", "websiteUri", "regularHours"]

    applied = await client.post(
        f"/api/v1/locations/{location_id}/edits", headers=headers, json=invalid
    )
    assert applied.status_code == 422
    assert "title" in applied.json()["detail"]["field_errors"]

    location = await read_location(session_factory, location_id)
    assert location.title == "Bandra Clinic"
    assert location.website_uri == "https://bandra.example.com"

    # A rejected attempt is still an attempt, so it is still audited.
    actions = await read_actions(session_factory, location_id)
    assert [action.status for action in actions] == ["failed"]


async def test_successful_apply_audits_and_updates_the_local_location(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)

    applied = await client.post(
        f"/api/v1/locations/{location_id}/edits",
        headers=headers,
        json={
            "title": "Bandra Dental Studio",
            "phone_primary": "+91 22 5550 0199",
            "open_status": "closed_temporarily",
            "hours_periods": [
                {
                    "open_day": "TUESDAY",
                    "open_hour": 8,
                    "open_minute": 30,
                    "close_day": "TUESDAY",
                    "close_hour": 13,
                },
                {"open_day": "FRIDAY", "open_hour": 20, "close_day": "SATURDAY", "close_hour": 2},
            ],
            "attributes": [
                {
                    "attribute_id": "has_wheelchair_accessible_entrance",
                    "value_type": "BOOL",
                    "values": [False],
                }
            ],
            "primary_category": {
                "category_name": "categories/gcid:orthodontist",
                "display_name": "Orthodontist",
            },
        },
    )
    assert applied.status_code == 201
    action = applied.json()
    assert action["status"] == "succeeded"
    assert action["action_type"] == "location_update"
    assert action["error"] is None
    assert action["user"]["email"] == "owner@example.com"
    assert action["payload"]["update_mask"] == [
        "title",
        "phoneNumbers",
        "openInfo",
        "regularHours",
        "attributes",
        "categories",
    ]

    detail = (await client.get(f"/api/v1/locations/{location_id}", headers=headers)).json()
    assert detail["title"] == "Bandra Dental Studio"
    assert detail["phone_primary"] == "+91 22 5550 0199"
    assert detail["open_status"] == "closed_temporarily"
    assert detail["primary_category_name"] == "categories/gcid:orthodontist"
    assert detail["categories"] == [
        {
            "category_name": "categories/gcid:orthodontist",
            "display_name": "Orthodontist",
            "is_primary": True,
        }
    ]
    # Regular hours are replaced wholesale, matching what the patch does at Google.
    assert {period["open_day"] for period in detail["hours_periods"]} == {"TUESDAY", "FRIDAY"}
    assert detail["attributes"] == [
        {
            "attribute_id": "has_wheelchair_accessible_entrance",
            "value_type": "BOOL",
            "values": [False],
        }
    ]

    stored = await read_actions(session_factory, location_id)
    assert [item.status for item in stored] == ["succeeded"]
    assert stored[0].google_response["response"]["validateOnly"] is False


async def test_failed_apply_audits_and_leaves_the_location_untouched(
    client: AsyncClient, session_factory, monkeypatch, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)

    provider = FailingProvider(UpdateResult(ok=False, error="Google is unavailable (503)"))
    monkeypatch.setattr("app.api.locations.get_provider", lambda: provider)

    applied = await client.post(
        f"/api/v1/locations/{location_id}/edits",
        headers=headers,
        json={"title": "Bandra Dental Studio"},
    )
    # An upstream refusal is a 502, never a 500.
    assert applied.status_code == 502
    assert applied.json()["detail"] == "Google is unavailable (503)"
    assert provider.calls == [False]

    assert (await read_location(session_factory, location_id)).title == "Bandra Clinic"
    actions = await read_actions(session_factory, location_id)
    assert [action.status for action in actions] == ["failed"]
    assert actions[0].error == "Google is unavailable (503)"
    assert actions[0].payload["update_mask"] == ["title"]


async def test_preview_uses_validate_only(
    client: AsyncClient, session_factory, monkeypatch, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)

    provider = FailingProvider(UpdateResult(ok=True))
    monkeypatch.setattr("app.api.locations.get_provider", lambda: provider)

    await client.post(
        f"/api/v1/locations/{location_id}/edits/preview",
        headers=headers,
        json={"title": "Bandra Dental Studio"},
    )
    assert provider.calls == [True]


async def test_action_history_is_newest_first_and_paginated(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)

    for title in ("First Rename", "Second Rename", "Third Rename"):
        response = await client.post(
            f"/api/v1/locations/{location_id}/edits", headers=headers, json={"title": title}
        )
        assert response.status_code == 201

    history = await client.get(f"/api/v1/locations/{location_id}/actions", headers=headers)
    assert history.status_code == 200
    titles = [action["payload"]["changes"][0]["proposed"] for action in history.json()]
    assert titles == ["Third Rename", "Second Rename", "First Rename"]
    assert all(action["status"] == "succeeded" for action in history.json())
    assert history.json()[0]["user"]["full_name"] == "Locus Owner"

    paged = await client.get(
        f"/api/v1/locations/{location_id}/actions",
        headers=headers,
        params={"limit": 1, "offset": 1},
    )
    assert [action["payload"]["changes"][0]["proposed"] for action in paged.json()] == [
        "Second Rename"
    ]


async def test_cross_organization_edits_return_404(
    client: AsyncClient, session_factory, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    await connect_google(organization_id)
    location_id = await seed_location(session_factory, organization_id)
    await client.post(
        f"/api/v1/locations/{location_id}/edits", headers=headers, json={"title": "Renamed"}
    )

    intruder, _ = await sign_in(client, "intruder@example.com", "Rival Group")
    assert (
        await client.post(
            f"/api/v1/locations/{location_id}/edits/preview",
            headers=intruder,
            json={"title": "Hijacked"},
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/locations/{location_id}/edits",
            headers=intruder,
            json={"title": "Hijacked"},
        )
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/locations/{location_id}/actions", headers=intruder)
    ).status_code == 404

    # The hijack attempts changed nothing and left no audit rows of their own.
    assert (await read_location(session_factory, location_id)).title == "Renamed"
    assert len(await read_actions(session_factory, location_id)) == 1


async def test_update_mask_is_derived_only_from_populated_changes() -> None:
    """The data-loss guard at its source: an unset field must never reach the mask."""
    assert build_update_mask(LocationChanges()) == []
    # An empty string is a deliberate clear, which is different from leaving a field out.
    assert build_update_mask(LocationChanges(website_uri="")) == ["websiteUri"]
    assert build_update_mask(LocationChanges(title="X", description="Y")) == ["title", "profile"]

    # The collection-valued fields each own one mask path, however many members they carry.
    everything = LocationChanges(
        title="Bandra Dental Studio",
        phone_primary="+91 22 5550 0199",
        description="Open Saturdays.",
        open_status=OpenStatus.closed_temporarily,
        hours_periods=(
            ProviderHoursPeriod(
                open_day="FRIDAY", open_hour=20, close_day="SATURDAY", close_hour=2, close_minute=30
            ),
        ),
        attributes=(
            ProviderAttribute(
                attribute_id="attributes/has_wifi", value_type="BOOL", values=(True,)
            ),
            ProviderAttribute(
                attribute_id="attributes/url_appointment",
                value_type="URL",
                values=("https://example.com/book",),
            ),
        ),
        primary_category=ProviderCategory(category_name="categories/gcid:orthodontist"),
    )
    assert build_update_mask(everything) == [
        "title",
        "phoneNumbers",
        "profile",
        "openInfo",
        "regularHours",
        "attributes",
        "categories",
    ]
