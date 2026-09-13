from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.api.dependencies import DbSession
from app.api.scoping import OrganizationId
from app.models import (
    AuditJob,
    AuditJobStatus,
    Location,
    Project,
    ProjectLocation,
    RecommendationRun,
)
from app.services.recommendations.contracts import SEMANTICS, field_contracts
from app.services.recommendations.policy import (
    CATEGORIES,
    CRITICAL_SCORE,
    ENUMERATED_FLOOR,
    RULE_DOCS,
    SEVERITY_PENALTY,
    WARNING_SCORE,
)
from app.services.recommendations.runs import latest_run, latest_runs, serialize
from app.services.recommendations.scoring import median
from app.services.recommendations.snapshot import fingerprint, read_snapshot
from app.services.recommendations.types import ENGINE_VERSION, GenerateRequest
from app.tasks.audit import generate_audit

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/contracts")
async def contracts(organization_id: OrganizationId):
    return {"engine_version": ENGINE_VERSION, "sources": field_contracts(), "semantics": SEMANTICS}


@router.get("/policy")
async def policy(organization_id: OrganizationId):
    """The scoring policy behind every health score, so the UI never hardcodes it."""
    return {
        "engine_version": ENGINE_VERSION,
        "categories": [
            {
                "category": name,
                "label": spec["label"],
                "weight": spec["weight"],
                "rules": spec["rules"],
            }
            for name, spec in CATEGORIES.items()
        ],
        "severity_bands": {"critical": CRITICAL_SCORE, "warning": WARNING_SCORE, "notice": 0},
        "severity_penalty": SEVERITY_PENALTY,
        "enumerated_floor": ENUMERATED_FLOOR,
        "grades": {"excellent": 90, "good": 75, "fair": 50, "poor": 0},
        "rules": [{"rule": rule, **docs} for rule, docs in RULE_DOCS.items()],
        "notes": [
            "Checks without enough evidence are excluded from the score, not scored as passes.",
            "Rules that enumerate every affected subject are scored on the share that failed.",
            "Scores order work. They are not predicted revenue, uplift or probability.",
        ],
    }


ACTIVE = (AuditJobStatus.pending, AuditJobStatus.running)


def serialize_job(job: AuditJob) -> dict:
    return {
        "id": str(job.id),
        "location_id": str(job.location_id),
        "status": job.status.value,
        "stage": job.stage,
        "progress": job.progress,
        "as_of": str(job.as_of),
        "run_id": str(job.run_id) if job.run_id else None,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


async def active_job(db, organization_id: UUID, location_id: UUID) -> AuditJob | None:
    return await db.scalar(
        select(AuditJob)
        .where(
            AuditJob.organization_id == organization_id,
            AuditJob.location_id == location_id,
            AuditJob.status.in_(ACTIVE),
        )
        .order_by(AuditJob.created_at.desc())
        .limit(1)
    )


async def owned_location(db, organization_id: UUID, location_id: UUID) -> Location:
    location = await db.scalar(
        select(Location).where(
            Location.id == location_id, Location.organization_id == organization_id
        )
    )
    if location is None:
        raise HTTPException(404, "Location not found")
    return location


@router.post("/runs", status_code=202)
async def create_run(payload: GenerateRequest, organization_id: OrganizationId, db: DbSession):
    """Queue an audit of one profile. Its previous audit stays readable until this lands."""
    today = datetime.now(UTC).date()
    as_of = payload.as_of or today
    if as_of > today:
        raise HTTPException(422, "Analysis date must not be in the future")
    await owned_location(db, organization_id, payload.location_id)
    running = await active_job(db, organization_id, payload.location_id)
    if running is not None:
        # One audit at a time per profile: two concurrent runs would compare against
        # the same prior audit and race to become that profile's current one.
        return serialize_job(running)
    job = AuditJob(
        organization_id=organization_id,
        location_id=payload.location_id,
        as_of=as_of,
        config=payload.config.model_dump(),
    )
    db.add(job)
    await db.commit()
    task = generate_audit.delay(str(job.id))
    job.task_id = task.id
    await db.commit()
    await db.refresh(job)
    return serialize_job(job)


@router.get("/jobs/{job_id}")
async def job_status(job_id: UUID, organization_id: OrganizationId, db: DbSession):
    job = await db.scalar(
        select(AuditJob).where(AuditJob.id == job_id, AuditJob.organization_id == organization_id)
    )
    if job is None:
        raise HTTPException(404, "Audit job not found")
    return serialize_job(job)


@router.get("/overview")
async def overview(
    organization_id: OrganizationId,
    db: DbSession,
    project_id: UUID | None = None,
):
    """Every profile with its own current audit, optionally narrowed to one project."""
    statement = select(Location).where(Location.organization_id == organization_id)
    if project_id is not None:
        # Validated against the organization so a project id cannot reach across tenants.
        owner = await db.scalar(
            select(Project.id).where(
                Project.id == project_id, Project.organization_id == organization_id
            )
        )
        if owner is None:
            raise HTTPException(404, "Project not found")
        statement = statement.join(
            ProjectLocation, ProjectLocation.location_id == Location.id
        ).where(ProjectLocation.project_id == project_id)
    locations = (await db.scalars(statement.order_by(Location.title))).all()
    scope = {location.id for location in locations}
    runs = {
        run.location_id: run
        for run in await latest_runs(db, organization_id)
        if run.location_id in scope
    }
    jobs = {
        job.location_id: job
        for job in (
            await db.scalars(
                select(AuditJob).where(
                    AuditJob.organization_id == organization_id, AuditJob.status.in_(ACTIVE)
                )
            )
        ).all()
    }
    items = []
    for location in locations:
        run = runs.get(location.id)
        summary = run.report["locations"][0] if run and run.report.get("locations") else None
        items.append(
            {
                "location_id": str(location.id),
                "name": location.title,
                "source_location_id": location.source_location_id,
                "audited_at": run.created_at.isoformat() if run else None,
                "as_of": str(run.as_of) if run else None,
                "engine_version": run.engine_version if run else None,
                "score": summary["health"]["score"] if summary else None,
                "grade": summary["health"]["grade"] if summary else None,
                "coverage": summary["health"]["coverage"] if summary else None,
                "issues": summary["count"] if summary else None,
                "severity": severity_counts(run) if run else {},
                "job": serialize_job(jobs[location.id]) if location.id in jobs else None,
            }
        )
    return {"items": items, "benchmark": benchmark(list(runs.values()))}


def severity_counts(run: RecommendationRun) -> dict:
    counts: dict[str, int] = {}
    for item in run.report["items"]:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    return counts


def benchmark(runs: list[RecommendationRun]) -> dict:
    """Compared against the other profiles in this organization, nothing external."""
    scores = [
        run.report["locations"][0]["health"]["score"]
        for run in runs
        if run.report.get("locations") and run.report["locations"][0]["health"]["score"] is not None
    ]
    return {
        "median_score": median(scores),
        "top_quartile_score": (
            sorted(scores)[max(0, round(len(scores) * 0.75) - 1)] if scores else None
        ),
        "locations_scored": len(scores),
        "basis": (
            "Compared against the other locations in this organization. "
            "No external or industry benchmark is used."
        ),
    }


@router.get("/latest")
async def latest(location_id: UUID, organization_id: OrganizationId, db: DbSession):
    """One profile's audit, plus any job still working on its next one."""
    await owned_location(db, organization_id, location_id)
    job = await active_job(db, organization_id, location_id)
    run = await latest_run(db, organization_id, location_id)
    payload = {
        "run": None,
        "inputs_changed": False,
        "job": serialize_job(job) if job else None,
        "benchmark": benchmark(await latest_runs(db, organization_id)),
    }
    if run is None:
        return payload
    current = await read_snapshot(db, organization_id, location_id)
    payload["run"] = serialize(run)
    payload["inputs_changed"] = (
        fingerprint(current) != run.fingerprint or run.engine_version != ENGINE_VERSION
    )
    return payload


async def owned_run(db, organization_id, run_id):
    run = await db.scalar(
        select(RecommendationRun).where(
            RecommendationRun.id == run_id, RecommendationRun.organization_id == organization_id
        )
    )
    if run is None:
        raise HTTPException(404, "Recommendation run not found")
    return run


@router.get("/runs/{run_id}")
async def detail(run_id: UUID, organization_id: OrganizationId, db: DbSession):
    return serialize(await owned_run(db, organization_id, run_id))


@router.get("/runs/{run_id}/evidence")
async def evidence(
    run_id: UUID,
    source: str,
    organization_id: OrganizationId,
    db: DbSession,
    recommendation_key: str,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    run = await owned_run(db, organization_id, run_id)
    item = next((r for r in run.report["items"] if r["key"] == recommendation_key), None)
    if item is None:
        raise HTTPException(404, "Recommendation not found")
    ids = {i for e in item["evidence"] if e["source"] == source for i in e["row_ids"]}
    rows = [r for r in run.snapshot.get(source, []) if r["id"] in ids]
    return {
        "items": rows[offset : offset + limit],
        "total": len(rows),
        "limit": limit,
        "offset": offset,
    }
