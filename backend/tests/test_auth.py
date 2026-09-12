"""Sessions for the one seeded account: login, refresh rotation, logout, `/auth/me`.

There is no registration endpoint — the application ships a single pre-seeded demo
account — so every test here starts from an account written straight into the database,
exactly as `app.seed` writes the real one.
"""

from conftest import PASSWORD, sign_in
from httpx import AsyncClient

EMAIL = "owner@example.com"


async def test_login_me_refresh_logout_flow(client: AsyncClient) -> None:
    headers, organization_id = await sign_in(client)

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == EMAIL
    assert body["full_name"] == "Locus Owner"
    assert body["organizations"] == [
        {
            "id": str(organization_id),
            "name": "Northstar Dental",
            "slug": "northstar-dental",
            "role": "owner",
        }
    ]

    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["user"]["email"] == EMAIL
    rotated = refreshed.json()["access_token"]

    logged_out = await client.post("/api/v1/auth/logout")
    assert logged_out.status_code == 200
    assert logged_out.json() == {"message": "Signed out"}

    # The refresh session is revoked, so the rotated cookie cannot be replayed.
    rejected_refresh = await client.post("/api/v1/auth/refresh")
    assert rejected_refresh.status_code == 401
    # The access token it already issued stays valid until it expires on its own.
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {rotated}"})
    ).status_code == 200


async def test_login_issues_an_httponly_refresh_cookie(client: AsyncClient) -> None:
    await sign_in(client)
    login = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    cookie = login.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    # The refresh credential is never handed to JavaScript.
    assert PASSWORD not in login.text


async def test_login_rejects_a_wrong_password_and_an_unknown_email(client: AsyncClient) -> None:
    await sign_in(client)

    wrong_password = await client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": "wrong-password"}
    )
    assert wrong_password.status_code == 401
    assert wrong_password.json()["detail"] == "Invalid email or password"

    unknown = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )
    assert unknown.status_code == 401


async def test_login_is_case_insensitive_on_the_email(client: AsyncClient) -> None:
    await sign_in(client)
    login = await client.post(
        "/api/v1/auth/login", json={"email": "OWNER@EXAMPLE.COM", "password": PASSWORD}
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == EMAIL


async def test_me_requires_a_token(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"})
    ).status_code == 401


async def test_registration_is_gone(client: AsyncClient) -> None:
    """One fixed account exists, so there is nothing to register."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "someone@example.com",
            "password": PASSWORD,
            "full_name": "Someone",
            "organization_name": "Somewhere",
        },
    )
    assert response.status_code == 404


async def test_health(client: AsyncClient) -> None:
    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
