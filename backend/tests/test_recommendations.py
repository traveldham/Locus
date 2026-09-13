from copy import deepcopy
from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from conftest import sign_in
from pydantic import ValidationError
from sqlalchemy import select

from app.models import Location, OpenStatus, RecommendationRun
from app.services.recommendations.engine import analyze, compare
from app.services.recommendations.types import EngineConfig
from app.tasks.audit import run_job

AS_OF = date(2026, 9, 11)


def data():
    return {
        "locations": [
            {
                "id": "location-x",
                "title": "An unrelated business",
                "open_status": "open",
                "has_voice_of_merchant": True,
                "phone_primary": "123456789",
                "website_uri": "https://example.org",
                "description": "Services",
                "primary_category_display": "Dentist",
            }
        ],
        "hours": [{"id": "h", "location_id": "location-x"}],
        "reviews": [
            {
                "id": f"r{i}",
                "location_id": "location-x",
                "star_rating": 2,
                "create_time": str(AS_OF - timedelta(days=5)),
                "reply_comment": None,
            }
            for i in range(5)
        ],
    }


def test_identical_inputs_reproduce_and_replies_remove_recommendations():
    snapshot = data()
    before = deepcopy(snapshot)
    original = analyze(snapshot, AS_OF)
    assert original == analyze(snapshot, AS_OF)
    assert snapshot == before
    assert any(r["rule"] == "reviews" for r in original["items"])
    for row in snapshot["reviews"]:
        row["reply_comment"] = "Responded"
    changed = analyze(snapshot, AS_OF)
    compare(changed, original)
    assert not any(r["rule"] == "reviews" for r in changed["items"])
    assert any(r["change"] == "no_longer_triggered" for r in changed["changes"])
    assert changed["fingerprint"] != original["fingerprint"]


def test_stale_evidence_is_not_mislabelled_resolved():
    snapshot = data()
    original = analyze(snapshot, AS_OF)
    later = analyze(snapshot, AS_OF + timedelta(days=90))
    compare(later, original)
    assert any(r["change"] == "cannot_evaluate" for r in later["changes"])
    assert not any(r["rule"] == "reviews" for r in later["items"])


def test_false_attributes_do_not_become_missing_and_closed_suppresses_growth():
    snapshot = data()
    snapshot["catalog"] = [{"id": "c", "attribute_name": "wifi", "applies_to_category": "Dentist"}]
    snapshot["attributes"] = [
        {
            "id": "a",
            "location_id": "location-x",
            "attribute_id": "attributes/wifi",
            "values": [False],
        }
    ]
    assert not any(r["rule"] == "attributes" for r in analyze(snapshot, AS_OF)["items"])
    snapshot["attributes"] = []
    assert any(r["rule"] == "attributes" for r in analyze(snapshot, AS_OF)["items"])
    snapshot["locations"][0]["open_status"] = "closed_permanently"
    assert not any(
        r["rule"] in ("profile", "attributes", "posts", "rankings", "performance")
        for r in analyze(snapshot, AS_OF)["items"]
    )


def test_performance_change_is_measured_and_missing_days_do_not_invent_decline():
    from app.services.recommendations.performance import ACTIONS, IMPRESSIONS

    snapshot = data()
    snapshot["performance"] = [
        {
            "id": f"p{i}",
            "location_id": "location-x",
            "date": str(AS_OF - timedelta(days=i)),
            **{key: 10 if i < 28 else 30 for key in (*IMPRESSIONS, *ACTIONS)},
        }
        for i in range(56)
    ]
    result = analyze(snapshot, AS_OF)
    item = next(r for r in result["items"] if r["rule"] == "performance")
    assert item["evidence"][0]["values"]["matched_days"] == 28
    assert item["evidence"][0]["values"]["current_impressions"] == 1120
    snapshot["performance"] = snapshot["performance"][14:]
    assert not any(r["rule"] == "performance" for r in analyze(snapshot, AS_OF)["items"])


def test_unknown_and_future_values_do_not_generate_actions():
    snapshot = data()
    snapshot["reviews"] = [{**r, "create_time": "2027-01-01"} for r in snapshot["reviews"]]
    snapshot["bookings"] = [
        {
            "id": "b",
            "location_id": "location-x",
            "status": "no_show",
            "requested_for_date": "2027-01-01",
            "booking_created_at": "2027-01-01",
        }
    ]
    assert not any(
        r["rule"] in ("reviews", "booking_outcomes", "booking_followup")
        for r in analyze(snapshot, AS_OF)["items"]
    )
    assert not any(r["rule"] == "media" for r in analyze(snapshot, AS_OF)["items"])


def test_configuration_changes_trigger_and_every_evidence_row_exists():
    snapshot = data()
    result = analyze(snapshot, AS_OF, EngineConfig(reply_wait_days=10))
    assert not any(r["rule"] == "reviews" for r in result["items"])
    for item in analyze(snapshot, AS_OF)["items"]:
        for e in item["evidence"]:
            ids = {r["id"] for r in snapshot[e["source"]]}
            assert set(e["row_ids"]) <= ids


def test_search_compares_exact_complete_months_and_never_fills_missing_with_zero():
    snapshot = data()
    snapshot["search_terms"] = [
        {
            "id": "s1",
            "location_id": "location-x",
            "search_term": "local service",
            "year_month": "2026-07",
            "impressions": 1000,
            "is_threshold": False,
        },
        {
            "id": "s2",
            "location_id": "location-x",
            "search_term": "local service",
            "year_month": "2026-08",
            "impressions": 500,
            "is_threshold": False,
        },
    ]
    assert any(r["rule"] == "search" for r in analyze(snapshot, AS_OF)["items"])
    snapshot["search_terms"][1]["is_threshold"] = True
    assert not any(r["rule"] == "search" for r in analyze(snapshot, AS_OF)["items"])
    snapshot["search_terms"].pop()
    assert not any(r["rule"] == "search" for r in analyze(snapshot, AS_OF)["items"])


def test_rank_not_found_is_not_zero_and_competitors_must_match_week():
    snapshot = data()
    snapshot["keywords"] = [{"id": "k", "location_id": "location-x", "keyword": "service"}]
    snapshot["ranks"] = [
        {
            "id": f"k{i}",
            "location_id": "location-x",
            "tracked_keyword_id": "k",
            "week_start": str(date(2026, 9, 7) - timedelta(weeks=i)),
            "found": False,
            "rank_absolute": None,
            "rank_in_local_pack": None,
        }
        for i in range(4)
    ]
    snapshot["competitors"] = [
        {"id": "c", "tracked_keyword_id": "k", "week_start": "2026-08-31", "rank_absolute": 1}
    ]
    item = next(r for r in analyze(snapshot, AS_OF)["items"] if r["rule"] == "rankings")
    assert item["evidence"][0]["values"]["outside_pack"] == 4
    assert not any(e["source"] == "competitors" for e in item["evidence"])
    snapshot["ranks"][0]["rank_absolute"] = 0
    assert not any(r["rule"] == "rankings" for r in analyze(snapshot, AS_OF)["items"])


def test_booking_denominator_excludes_unsettled_and_future_appointments():
    snapshot = data()
    snapshot["bookings"] = [
        {
            "id": f"b{i}",
            "location_id": "location-x",
            "booking_created_at": "2026-09-01",
            "requested_for_date": "2026-09-10",
            "status": "no_show" if i < 5 else "completed",
        }
        for i in range(20)
    ]
    snapshot["bookings"] += [
        {
            "id": "future",
            "location_id": "location-x",
            "booking_created_at": "2026-09-01",
            "requested_for_date": "2026-09-12",
            "status": "no_show",
        },
        {
            "id": "unsettled",
            "location_id": "location-x",
            "booking_created_at": "2026-09-01",
            "requested_for_date": "2026-09-10",
            "status": "confirmed",
        },
    ]
    item = next(r for r in analyze(snapshot, AS_OF)["items"] if r["rule"] == "booking_outcomes")
    assert item["evidence"][0]["values"]["rate"] == 0.25
    assert len(item["evidence"][0]["row_ids"]) == 20
    for row in snapshot["bookings"]:
        row["status"] = "completed"
    assert not any(r["rule"] == "booking_outcomes" for r in analyze(snapshot, AS_OF)["items"])


def test_media_unknown_and_empty_attribute_values_abstain_or_request_confirmation():
    snapshot = data()
    snapshot["media"] = [{"id": "m", "location_id": "location-x", "has_cover_photo": None}]
    report = analyze(snapshot, AS_OF)
    assert (
        next(e for e in report["evaluations"] if e["rule"] == "media")["state"]
        == "insufficient_data"
    )
    snapshot["catalog"] = [{"id": "c", "attribute_name": "wifi", "applies_to_category": "Dentist"}]
    snapshot["attributes"] = [
        {"id": "a", "location_id": "location-x", "attribute_id": "attributes/wifi", "values": []}
    ]
    assert any(r["rule"] == "attributes" for r in analyze(snapshot, AS_OF)["items"])


def test_policy_requires_weekday_aligned_windows_and_finite_numbers():
    from app.services.recommendations.context import number

    with pytest.raises(ValidationError):
        EngineConfig(window_days=15)
    assert not number(float("nan"))
    assert not number(float("inf"))


def test_contracts_cover_every_model_column():
    from app.services.recommendations.contracts import TABLES, field_contracts

    contracts = field_contracts()
    for source, model in TABLES.items():
        assert set(contracts[source]["fields"]) == {c.key for c in model.__table__.columns}


async def test_run_api_history_staleness_evidence_and_tenant_isolation(
    client, session_factory, stub_queue
):
    headers, org = await sign_in(client)
    async with session_factory() as db:
        location = Location(
            organization_id=org,
            title="Test business",
            google_location_name="locations/test",
            open_status=OpenStatus.open,
        )
        db.add(location)
        await db.commit()
        location_id = location.id
    assert (
        await client.get("/api/v1/recommendations/latest", params={"location_id": str(location_id)})
    ).status_code == 401
    empty = (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()
    assert empty["run"] is None and empty["job"] is None

    response = await client.post(
        "/api/v1/recommendations/runs",
        headers=headers,
        json={"location_id": str(location_id), "as_of": str(AS_OF)},
    )
    assert response.status_code == 202, response.text
    job = response.json()
    assert job["status"] == "pending" and job["progress"] == 0
    assert stub_queue == [job["id"]]
    # Queued, not run: nothing is published until the worker finishes, and the job is
    # advertised on /latest so a reload still knows an audit is in flight.
    pending = (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()
    assert pending["run"] is None and pending["job"]["id"] == job["id"]
    assert pending["job"]["location_id"] == str(location_id)
    # A second request joins the running job rather than starting a competing audit.
    again = await client.post(
        "/api/v1/recommendations/runs",
        headers=headers,
        json={"location_id": str(location_id), "as_of": str(AS_OF)},
    )
    assert again.json()["id"] == job["id"] and stub_queue == [job["id"]]

    await run_job(UUID(job["id"]), session_factory)
    finished = (
        await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)
    ).json()
    assert finished["status"] == "succeeded" and finished["progress"] == 100
    assert finished["stage"] == "Done" and finished["run_id"]
    run = (
        await client.get(f"/api/v1/recommendations/runs/{finished['run_id']}", headers=headers)
    ).json()
    assert len(run["locations"]) == 1
    assert run["items"]
    latest = (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()
    assert not latest["inputs_changed"]
    assert latest["run"]["location_id"] == str(location_id)
    # The benchmark comes from the other profiles' audits, not from this report.
    assert latest["benchmark"]["locations_scored"] == 1
    assert "No external or industry benchmark" in latest["benchmark"]["basis"]
    directory = (await client.get("/api/v1/recommendations/overview", headers=headers)).json()
    assert [row["location_id"] for row in directory["items"]] == [str(location_id)]
    assert directory["items"][0]["issues"] == len(run["items"])
    assert directory["items"][0]["audited_at"] and directory["items"][0]["job"] is None
    policy = (await client.get("/api/v1/recommendations/policy", headers=headers)).json()
    assert sum(c["weight"] for c in policy["categories"]) == 100
    assert policy["severity_bands"]["critical"] == 75
    key = run["items"][0]["key"]
    ev = await client.get(
        f"/api/v1/recommendations/runs/{run['id']}/evidence",
        headers=headers,
        params={"source": "locations", "recommendation_key": key},
    )
    assert ev.status_code == 200 and ev.json()["total"] == 1
    async with session_factory() as db:
        location = await db.get(Location, location_id)
        location.website_uri = "https://example.org"
        await db.commit()
    assert (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()["inputs_changed"]
    archived = (
        await client.get(f"/api/v1/recommendations/runs/{run['id']}", headers=headers)
    ).json()
    assert archived["fingerprint"] == run["fingerprint"]
    old_evidence = (
        await client.get(
            f"/api/v1/recommendations/runs/{run['id']}/evidence",
            headers=headers,
            params={"source": "locations", "recommendation_key": key},
        )
    ).json()
    assert old_evidence["items"][0]["website_uri"] is None
    assert "organization_id" not in old_evidence["items"][0]
    assert (
        await client.post(
            "/api/v1/recommendations/runs",
            headers=headers,
            json={"location_id": str(location_id), "as_of": "2999-01-01"},
        )
    ).status_code == 422
    intruder, _ = await sign_in(client, "other@example.org", "Another business")
    assert (
        await client.get(f"/api/v1/recommendations/runs/{run['id']}", headers=intruder)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/recommendations/runs/{uuid4()}", headers=headers)
    ).status_code == 404
    # A job belongs to its organization, and an unknown one is not found.
    assert (
        await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=intruder)
    ).status_code == 404
    # Auditing someone else's profile is a not-found, not a silent cross-tenant run.
    assert (
        await client.post(
            "/api/v1/recommendations/runs",
            headers=intruder,
            json={"location_id": str(location_id), "as_of": str(AS_OF)},
        )
    ).status_code == 404
    assert (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=intruder,
            params={"location_id": str(location_id)},
        )
    ).status_code == 404
    assert (await client.get("/api/v1/recommendations/overview", headers=intruder)).json()[
        "items"
    ] == []
    assert (
        await client.get(f"/api/v1/recommendations/jobs/{uuid4()}", headers=headers)
    ).status_code == 404


async def test_only_the_current_audit_is_kept(client, session_factory, stub_queue):
    """No audit history: a new run replaces the old one rather than stacking up."""
    headers, org = await sign_in(client)
    async with session_factory() as db:
        location = Location(
            organization_id=org,
            title="Test business",
            google_location_name="locations/test",
            open_status=OpenStatus.open,
        )
        db.add(location)
        await db.commit()
        location_id = location.id

    async def audit() -> str:
        response = await client.post(
            "/api/v1/recommendations/runs",
            headers=headers,
            json={"location_id": str(location_id), "as_of": str(AS_OF)},
        )
        job = response.json()
        await run_job(UUID(job["id"]), session_factory)
        finished = (
            await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)
        ).json()
        assert finished["status"] == "succeeded", finished
        return finished["run_id"]

    first = await audit()
    second = await audit()
    assert first != second

    async with session_factory() as db:
        stored = (await db.scalars(select(RecommendationRun.id))).all()
    assert [str(run_id) for run_id in stored] == [second]

    # The replaced audit is gone, and only the current one answers.
    assert (
        await client.get(f"/api/v1/recommendations/runs/{first}", headers=headers)
    ).status_code == 404
    latest = (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()
    assert latest["run"]["id"] == second


async def test_new_profiles_are_audited_automatically(client, session_factory, stub_queue):
    """A profile entering a project should not sit unaudited behind an empty screen."""
    headers, org = await sign_in(client)
    async with session_factory() as db:
        first = Location(
            organization_id=org,
            title="First profile",
            google_location_name="locations/one",
            open_status=OpenStatus.open,
        )
        second = Location(
            organization_id=org,
            title="Second profile",
            google_location_name="locations/two",
            open_status=OpenStatus.open,
        )
        db.add_all([first, second])
        await db.commit()
        first_id, second_id = str(first.id), str(second.id)

    created = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Launch", "location_ids": [first_id]},
    )
    assert created.status_code == 201, created.text
    assert len(stub_queue) == 1
    queued = (await client.get("/api/v1/recommendations/overview", headers=headers)).json()
    audit = next(row for row in queued["items"] if row["location_id"] == first_id)
    assert audit["job"]["status"] == "pending" and audit["score"] is None

    # Adding the second profile queues only that one.
    project_id = created.json()["id"]
    added = await client.post(
        f"/api/v1/projects/{project_id}/locations",
        headers=headers,
        json={"location_ids": [second_id]},
    )
    assert added.status_code == 200, added.text
    assert len(stub_queue) == 2

    # Filing them under a second project audits them again, so that project never opens
    # onto a result produced days ago for someone else.
    for job_id in list(stub_queue):
        await run_job(UUID(job_id), session_factory)
    again = await client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Second folder", "location_ids": [first_id, second_id]},
    )
    assert again.status_code == 201, again.text
    assert len(stub_queue) == 4

    # The audit still belongs to the profile, not the project: one run each, shared.
    async with session_factory() as db:
        stored = (await db.scalars(select(RecommendationRun.location_id))).all()
    assert sorted(str(x) for x in stored) == sorted([first_id, second_id])

    # The directory narrows to a project rather than showing the whole organization.
    scoped = (
        await client.get(
            "/api/v1/recommendations/overview",
            headers=headers,
            params={"project_id": project_id},
        )
    ).json()
    assert {row["location_id"] for row in scoped["items"]} == {first_id, second_id}
    assert all(row["score"] is not None for row in scoped["items"])


async def test_every_list_narrows_to_the_active_project(client, session_factory, stub_queue):
    """A project is a scope, not a label: the lists honour it the same way."""
    headers, org = await sign_in(client)
    async with session_factory() as db:
        inside = Location(
            organization_id=org,
            title="Inside the project",
            google_location_name="locations/in",
            open_status=OpenStatus.open,
        )
        outside = Location(
            organization_id=org,
            title="Outside the project",
            google_location_name="locations/out",
            open_status=OpenStatus.open,
        )
        db.add_all([inside, outside])
        await db.commit()
        inside_id = str(inside.id)

    project_id = (
        await client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "Scoped", "location_ids": [inside_id]},
        )
    ).json()["id"]

    for path in ("/api/v1/locations", "/api/v1/posts", "/api/v1/bookings"):
        scoped = await client.get(path, headers=headers, params={"project_id": project_id})
        assert scoped.status_code == 200, f"{path}: {scoped.text}"
        rows = scoped.json()
        items = rows if isinstance(rows, list) else rows["items"]
        assert all(row.get("location_id", inside_id) == inside_id for row in items), (
            f"{path} leaked a location outside the project"
        )

    # Both locations are visible without a project, so the filter is doing the work.
    everything = (await client.get("/api/v1/locations", headers=headers)).json()
    assert len(everything) == 2

    # Another tenant's project id is a not-found, never a silent cross-tenant read.
    intruder, _ = await sign_in(client, "other@example.org", "Another business")
    for path in ("/api/v1/locations", "/api/v1/posts", "/api/v1/bookings"):
        blocked = await client.get(path, headers=intruder, params={"project_id": project_id})
        assert blocked.status_code == 404, f"{path} allowed a cross-tenant project"
