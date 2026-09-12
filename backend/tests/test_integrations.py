"""The Google connection, which is now only ever read.

Nothing authorizes, imports or disconnects any more: `app.seed` writes one connection row
and `GET /integrations/google` hands it back so the UI can show the integration as
connected.
"""

from conftest import sign_in
from httpx import AsyncClient

from app.api.integrations import router as integrations_router
from app.core.config import get_settings
from app.main import app


def _ensure_router_registered() -> None:
    """main.py is owned elsewhere; register the router here if it has not been yet."""
    prefix = f"{get_settings().api_prefix}/integrations/google"
    if not any(getattr(route, "path", "").startswith(prefix) for route in app.routes):
        app.include_router(integrations_router, prefix=get_settings().api_prefix)


_ensure_router_registered()


async def test_reading_the_connection_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/integrations/google")).status_code == 401


async def test_the_oauth_endpoints_are_gone(client: AsyncClient) -> None:
    """Authorize, callback, discovery, import and disconnect no longer exist."""
    headers, _ = await sign_in(client)
    for method, path in (
        ("get", "/api/v1/integrations/google/authorize"),
        ("get", "/api/v1/integrations/google/callback"),
        ("get", "/api/v1/integrations/google/discovery"),
        ("post", "/api/v1/integrations/google/import"),
        ("delete", "/api/v1/integrations/google"),
        ("get", "/api/v1/auth/google/authorize"),
        ("post", "/api/v1/onboarding/organization"),
    ):
        response = await getattr(client, method)(path, headers=headers)
        assert response.status_code in (404, 405), path


async def test_connection_is_null_until_the_seed_writes_one(client: AsyncClient) -> None:
    headers, _ = await sign_in(client)
    response = await client.get("/api/v1/integrations/google", headers=headers)
    assert response.status_code == 200
    assert response.json() is None


async def test_the_seeded_connection_reads_back_as_connected(
    client: AsyncClient, connect_google
) -> None:
    headers, organization_id = await sign_in(client)
    connection_id = await connect_google(organization_id)

    response = await client.get("/api/v1/integrations/google", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(connection_id)
    assert body["status"] == "active"
    assert body["google_account_email"] == "owner@example.com"
    assert body["scopes"] == ["https://www.googleapis.com/auth/business.manage"]
    assert body["connected_at"]
    # The stored refresh-token placeholder is never part of the response.
    assert "refresh" not in response.text


async def test_another_organizations_connection_is_not_visible(
    client: AsyncClient, connect_google
) -> None:
    _, organization_id = await sign_in(client)
    await connect_google(organization_id)

    intruder, _ = await sign_in(client, "intruder@example.com", "Rival Group")
    response = await client.get("/api/v1/integrations/google", headers=intruder)
    assert response.status_code == 200
    assert response.json() is None
