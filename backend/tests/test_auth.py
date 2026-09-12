from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "email": "owner@example.com",
    "password": "correct-horse-battery-staple",
    "full_name": "Locus Owner",
    "organization_name": "Northstar Dental",
}


async def test_register_me_refresh_logout_flow(client: AsyncClient) -> None:
    registered = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert registered.status_code == 201
    body = registered.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == REGISTER_PAYLOAD["email"]
    assert body["user"]["organizations"] == [
        {
            "id": body["user"]["organizations"][0]["id"],
            "name": "Northstar Dental",
            "slug": "northstar-dental",
            "role": "owner",
        }
    ]
    assert "HttpOnly" in registered.headers["set-cookie"]
    assert "SameSite=lax" in registered.headers["set-cookie"]

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["full_name"] == "Locus Owner"

    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != body["access_token"]

    logged_out = await client.post("/api/v1/auth/logout")
    assert logged_out.status_code == 200
    assert logged_out.json() == {"message": "Signed out"}

    rejected_refresh = await client.post("/api/v1/auth/refresh")
    assert rejected_refresh.status_code == 401


async def test_login_and_authentication_failures(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    duplicate = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert duplicate.status_code == 409

    wrong_password = await client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrong-password"},
    )
    assert wrong_password.status_code == 401

    missing_token = await client.get("/api/v1/auth/me")
    assert missing_token.status_code == 401

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "OWNER@EXAMPLE.COM", "password": REGISTER_PAYLOAD["password"]},
    )
    assert login.status_code == 200


async def test_health_and_registration_validation(client: AsyncClient) -> None:
    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    invalid = await client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "full_name": "   "},
    )
    assert invalid.status_code == 422
