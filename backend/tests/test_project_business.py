from types import SimpleNamespace

from conftest import sign_in

from app.sample_business import populate_business


async def test_business_fields_round_trip_and_patch_preserves_or_clears(client):
    headers, _ = await sign_in(client)
    payload = {
        "name": "Dental Business",
        "website_url": "https://example.com",
        "description": "  General dentistry and orthodontics.  ",
        "services": ["Dentistry", " Orthodontics ", "dentistry"],
    }
    response = await client.post("/api/v1/projects", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    project = response.json()
    assert project["website_url"] == "https://example.com/"
    assert project["services"] == ["Dentistry", "Orthodontics"]
    assert project["description"] == payload["description"].strip()
    path = f"/api/v1/projects/{project['id']}"
    assert (await client.get(path, headers=headers)).json()["services"] == project["services"]
    listed = (await client.get("/api/v1/projects", headers=headers)).json()[0]
    assert listed["website_url"] == project["website_url"]
    renamed = (await client.patch(path, headers=headers, json={"name": "New name"})).json()
    assert renamed["services"] == project["services"]
    assert renamed["website_url"] == project["website_url"]
    assert renamed["slug"] == project["slug"]
    cleared = (
        await client.patch(
            path,
            headers=headers,
            json={
                "website_url": None,
                "description": "",
                "services": [],
            },
        )
    ).json()
    assert cleared["website_url"] is None and cleared["description"] is None
    assert cleared["services"] == []
    other, _ = await sign_in(client, "business-other@example.org", "Other business")
    assert (await client.patch(path, headers=other, json=payload)).status_code == 404


async def test_business_validation(client):
    headers, _ = await sign_in(client)
    for fields in [
        {"website_url": "javascript:alert(1)"},
        {"website_url": "not-a-url"},
        {"website_url": "https://user:password@example.com"},
        {"services": [" "]},
        {"services": ["a" * 121]},
        {"services": [str(i) for i in range(101)]},
        {"services": None},
        {"description": "x" * 5001},
    ]:
        response = await client.post(
            "/api/v1/projects", headers=headers, json={"name": "Business", **fields}
        )
        assert response.status_code == 422, response.text


def test_demo_business_backfill_is_repeatable_and_preserves_edits():
    project = SimpleNamespace(website_url=None, services=[], description=None)
    populate_business(project)
    assert project.website_url.startswith("https://")
    assert project.services and "synthetic" in project.description
    previous = vars(project).copy()
    populate_business(project)
    assert vars(project) == previous
    project.website_url = "https://operator.example/"
    project.services = ["Confirmed service"]
    project.description = "Operator description"
    populate_business(project)
    assert project.website_url == "https://operator.example/"
    assert project.services == ["Confirmed service"]
    assert project.description == "Operator description"
