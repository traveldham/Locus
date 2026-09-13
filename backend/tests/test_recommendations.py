"""The audit pipeline: one job, six workers, one published run per profile."""

from datetime import date
from uuid import UUID, uuid4

import pytest
from conftest import sign_in
from pydantic import ValidationError
from sqlalchemy import select

from app.models import AuditJob, AuditJobStatus, Location, OpenStatus, RecommendationRun
from app.services.recommendations.categories import WORKERS
from app.services.recommendations.engine import analyze
from app.services.recommendations.policy import CATEGORIES
from app.services.recommendations.types import EngineConfig
from app.tasks.audit import finish_job, prepare_job, run_category, run_job

AS_OF = date(2026, 9, 11)
KEYS = [worker.KEY for worker in WORKERS]


def data():
    return {
        "locations": [
            {
                "id": "location-x",
                "title": "An unrelated business",
                "open_status": "open",
                "source": "fixture",
                "source_location_id": "LOC-X",
            }
        ]
    }


async def make_location(session_factory, org, title="Test business") -> UUID:
    async with session_factory() as db:
        location = Location(
            organization_id=org,
            title=title,
            google_location_name=f"locations/{uuid4()}",
            open_status=OpenStatus.open,
        )
        db.add(location)
        await db.commit()
        return location.id


def test_six_workers_in_a_fixed_order_with_weights_summing_to_100():
    assert KEYS == ["profile", "reputation", "visibility", "operations", "performance", "content"]
    assert list(CATEGORIES) == KEYS
    assert sum(spec["weight"] for spec in CATEGORIES.values()) == 100


def test_every_worker_assesses_every_check_it_declares():
    """A bare profile: each worker assesses all of its checks, and only its own."""
    report = analyze(data(), AS_OF)
    assessed = {(e["category"], e["rule"]) for e in report["evaluations"]}
    for worker in WORKERS:
        assert {(worker.KEY, rule) for rule in worker.CHECKS} <= assessed
    assert {i["category"] for i in report["items"]} <= set(KEYS)
    health = report["location"]["health"]
    assert health["score"] is not None and health["score"] < 50
    assert [c["category"] for c in health["categories"]] == KEYS
    by_category = {c["category"]: c for c in health["categories"]}
    assert by_category["profile"]["score"] is not None
    assert {row["category"] for row in report["location"]["by_rule"]} == set(KEYS)
    assert report["location"]["name"] == "An unrelated business"
    assert report["counts"] == {"locations": 1}
    # Same inputs, same report.
    assert analyze(data(), AS_OF) == report


def test_config_rejects_unknown_thresholds():
    with pytest.raises(ValidationError):
        EngineConfig(anything=1)


async def test_pipeline_runs_six_workers_and_publishes_one_run(client, session_factory, stub_queue):
    headers, org = await sign_in(client)
    location_id = await make_location(session_factory, org)

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
    assert empty == {"run": None, "inputs_changed": False, "job": None, "history": []}

    response = await client.post(
        "/api/v1/recommendations/runs",
        headers=headers,
        json={"location_id": str(location_id), "as_of": str(AS_OF)},
    )
    assert response.status_code == 202, response.text
    job = response.json()
    assert job["status"] == "pending" and job["progress"] == 0 and job["stage"] == "Queued"
    assert [w["category"] for w in job["workers"]] == KEYS
    assert all(w["status"] == "pending" for w in job["workers"])
    assert stub_queue == [job["id"]]

    # Queued, not run: nothing is published, and /latest advertises the job.
    pending = (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()
    assert pending["run"] is None and pending["job"]["id"] == job["id"]

    # A second request joins the running pipeline rather than starting a competing one.
    again = await client.post(
        "/api/v1/recommendations/runs",
        headers=headers,
        json={"location_id": str(location_id), "as_of": str(AS_OF)},
    )
    assert again.json()["id"] == job["id"] and stub_queue == [job["id"]]

    # Step through the pipeline the way the Celery chord does.
    job_id = UUID(job["id"])
    assert await prepare_job(job_id, session_factory)
    started = (
        await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)
    ).json()
    assert started["status"] == "running" and started["stage"] == "0 of 6 workers finished"

    await run_category(job_id, "profile", session_factory)
    await run_category(job_id, "content", session_factory)
    partial = (
        await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)
    ).json()
    assert partial["stage"] == "2 of 6 workers finished" and partial["progress"] == 33
    by_category = {w["category"]: w for w in partial["workers"]}
    assert by_category["profile"]["status"] == "succeeded"
    assert by_category["content"]["status"] == "succeeded"
    assert by_category["reputation"]["status"] == "pending"

    # Finishing before every worker has reported does nothing.
    await finish_job(job_id, session_factory)
    assert (await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)).json()[
        "status"
    ] == "running"

    for key in KEYS:
        await run_category(job_id, key, session_factory)
    await finish_job(job_id, session_factory)

    finished = (
        await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)
    ).json()
    assert finished["status"] == "succeeded" and finished["progress"] == 100
    assert finished["stage"] == "Done" and finished["run_id"]
    assert all(w["status"] == "succeeded" for w in finished["workers"])

    run = (
        await client.get(f"/api/v1/recommendations/runs/{finished['run_id']}", headers=headers)
    ).json()
    assert run["location_id"] == str(location_id)
    assert run["location"]["health"]["score"] is not None
    assert run["items"] and all(i["suggestion"] is None for i in run["items"])
    # No Gemini key in tests: the suggestion pass is skipped, never attempted.
    async with session_factory() as db:
        from app.models import AuditWorker

        workers = (await db.scalars(select(AuditWorker))).all()
        statuses = {w.category: w.result["suggestions"]["status"] for w in workers}
        assert statuses["profile"] == "skipped"
    latest = (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()
    assert latest["run"]["id"] == run["id"] and latest["job"] is None
    assert not latest["inputs_changed"]

    directory = (await client.get("/api/v1/recommendations/overview", headers=headers)).json()
    assert [row["location_id"] for row in directory["items"]] == [str(location_id)]
    row = directory["items"][0]
    assert row["issues"] > 0 and row["score"] is not None and row["audited_at"]
    assert row["job"] is None

    policy = (await client.get("/api/v1/recommendations/policy", headers=headers)).json()
    assert sum(c["weight"] for c in policy["categories"]) == 100
    assert {r["rule"] for r in policy["rules"]} == {
        rule for worker in WORKERS for rule in worker.CHECKS
    }

    # Changing an input the snapshot covers makes the audit stale.
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

    assert (
        await client.post(
            "/api/v1/recommendations/runs",
            headers=headers,
            json={"location_id": str(location_id), "as_of": "2999-01-01"},
        )
    ).status_code == 422


async def test_a_failed_worker_fails_the_pipeline_and_names_itself(
    client, session_factory, stub_queue, monkeypatch
):
    headers, org = await sign_in(client)
    location_id = await make_location(session_factory, org)
    job = (
        await client.post(
            "/api/v1/recommendations/runs",
            headers=headers,
            json={"location_id": str(location_id), "as_of": str(AS_OF)},
        )
    ).json()

    def explode(snapshot, as_of, config, category):
        if category == "reputation":
            raise RuntimeError("boom")
        return {"category": category, "items": [], "evaluations": []}

    monkeypatch.setattr("app.tasks.audit.run_worker", explode)
    await run_job(UUID(job["id"]), session_factory)

    failed = (await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)).json()
    assert failed["status"] == "failed" and failed["run_id"] is None
    assert "reputation (RuntimeError: boom)" in failed["error"]
    workers = {w["category"]: w for w in failed["workers"]}
    assert workers["reputation"]["status"] == "failed"
    assert workers["reputation"]["error"] == "RuntimeError: boom"
    assert workers["profile"]["status"] == "succeeded"
    # Nothing was published.
    async with session_factory() as db:
        assert (await db.scalars(select(RecommendationRun.id))).all() == []
    # The failed pipeline is no longer active, so a rerun starts fresh.
    rerun = (
        await client.post(
            "/api/v1/recommendations/runs",
            headers=headers,
            json={"location_id": str(location_id), "as_of": str(AS_OF)},
        )
    ).json()
    assert rerun["id"] != job["id"]


async def test_only_the_current_audit_is_kept(client, session_factory, stub_queue):
    """No audit history: a new run replaces the old one rather than stacking up."""
    headers, org = await sign_in(client)
    location_id = await make_location(session_factory, org)

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
    # Fix something between audits so "fixed since last audit" has something to say.
    async with session_factory() as db:
        location = await db.get(Location, location_id)
        location.website_uri = "https://example.org"
        await db.commit()
    second = await audit()
    assert first != second

    latest_payload = (
        await client.get(
            "/api/v1/recommendations/latest",
            headers=headers,
            params={"location_id": str(location_id)},
        )
    ).json()
    assert [point["run_id"] for point in latest_payload["history"]] == [first, second]
    changes = latest_payload["run"]["location"]["changes"]
    assert not changes["first_audit"] and changes["previous_audit_at"]
    assert "website_missing" in changes["fixed"]
    assert changes["previous_state"]["website_missing"] == "triggered"
    assert latest_payload["run"]["location"]["summaries"]["profile"]["source"] == "deterministic"
    assert latest_payload["run"]["location"]["summary"]["source"] == "deterministic"
    assert latest_payload["run"]["location"]["priorities"]

    async with session_factory() as db:
        stored = (await db.scalars(select(RecommendationRun.id))).all()
        assert [str(run_id) for run_id in stored] == [second]
        # The finished job no longer carries the snapshot; the run does.
        jobs = (await db.scalars(select(AuditJob))).all()
        assert all(job.snapshot is None for job in jobs)
        assert all(job.status == AuditJobStatus.succeeded for job in jobs)

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


async def test_tenant_isolation(client, session_factory, stub_queue):
    headers, org = await sign_in(client)
    location_id = await make_location(session_factory, org)
    job = (
        await client.post(
            "/api/v1/recommendations/runs",
            headers=headers,
            json={"location_id": str(location_id), "as_of": str(AS_OF)},
        )
    ).json()
    await run_job(UUID(job["id"]), session_factory)
    run_id = (
        await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=headers)
    ).json()["run_id"]

    intruder, _ = await sign_in(client, "other@example.org", "Another business")
    assert (
        await client.get(f"/api/v1/recommendations/runs/{run_id}", headers=intruder)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/recommendations/runs/{uuid4()}", headers=headers)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/recommendations/jobs/{job['id']}", headers=intruder)
    ).status_code == 404
    assert (
        await client.get(f"/api/v1/recommendations/jobs/{uuid4()}", headers=headers)
    ).status_code == 404
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
        await client.get(
            f"/api/v1/recommendations/runs/{run_id}/evidence",
            headers=headers,
            params={"source": "locations", "recommendation_key": "nope"},
        )
    ).status_code == 404


async def test_new_profiles_are_audited_automatically(client, session_factory, stub_queue):
    """A profile entering a project should not sit unaudited behind an empty screen."""
    headers, org = await sign_in(client)
    first_id = str(await make_location(session_factory, org, "First profile"))
    second_id = str(await make_location(session_factory, org, "Second profile"))

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
    assert len(audit["job"]["workers"]) == 6

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

    scoped = (
        await client.get(
            "/api/v1/recommendations/overview",
            headers=headers,
            params={"project_id": project_id},
        )
    ).json()
    assert {row["location_id"] for row in scoped["items"]} == {first_id, second_id}
    assert all(row["audited_at"] for row in scoped["items"])


async def test_every_list_narrows_to_the_active_project(client, session_factory, stub_queue):
    """A project is a scope, not a label: the lists honour it the same way."""
    headers, org = await sign_in(client)
    inside_id = str(await make_location(session_factory, org, "Inside the project"))
    await make_location(session_factory, org, "Outside the project")

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

    everything = (await client.get("/api/v1/locations", headers=headers)).json()
    assert len(everything) == 2

    intruder, _ = await sign_in(client, "other@example.org", "Another business")
    for path in ("/api/v1/locations", "/api/v1/posts", "/api/v1/bookings"):
        blocked = await client.get(path, headers=intruder, params={"project_id": project_id})
        assert blocked.status_code == 404, f"{path} allowed a cross-tenant project"
