"""Write generated profiles into the database, through the models, idempotently.

Every row goes in as a mapped object so relationships, enums and constraints are all
respected — nothing here reaches for raw SQL. The original sample dataset in
`locus-intelligence-assignment/data/` is never touched: these profiles are additions, and
they carry their own attribute catalog under their own Google category so the twelve
seeded clinics' attribute coverage and competitor medians are left exactly as they were.

**How an imported profile is marked.** `Location.source` is set to `LocationSource.fixture`,
which the model already carries for data that did not come from Google, and the natural
key `google_location_name = "locations/demo-<key>"` both identifies the archetype and
makes the import idempotent: the unique constraint on `(organization_id,
google_location_name)` means a second import of the same key finds the row and skips it.
Every analytics row hangs off that location, and each is written with
`DataSource.locus` — these numbers were produced here, not by Google, and the provenance
mark is what stops the UI implying otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AttributeCatalogItem,
    Booking,
    BookingChannel,
    BookingStatus,
    CompetitorObservation,
    DataSource,
    KeywordRank,
    Location,
    LocationAttributeValue,
    LocationCategory,
    LocationHoursPeriod,
    LocationSource,
    MediaSummary,
    OpenStatus,
    Organization,
    PerformanceDaily,
    Post,
    PostCtaType,
    PostType,
    Project,
    ProjectLocation,
    Review,
    SearchIntent,
    SearchTermMonthly,
    TrackedKeyword,
)
from generator_data.archetypes import ARCHETYPES, KEYS, Archetype, by_key
from generator_data.generator import ProfileData, generate

# The natural key that identifies an imported archetype inside one organization.
NAME_PREFIX = "locations/demo-"


def location_name(key: str) -> str:
    return f"{NAME_PREFIX}{key}"


def key_of(location: Location) -> str | None:
    name = location.google_location_name or ""
    return name.removeprefix(NAME_PREFIX) if name.startswith(NAME_PREFIX) else None


@dataclass
class ImportResult:
    """What one import call did, keyed so a caller can link each profile to its audit."""

    imported: list[dict] = field(default_factory=list)  # [{"key": ..., "location_id": "<uuid>"}]
    skipped: list[str] = field(default_factory=list)  # keys this organization already has
    unknown: list[str] = field(default_factory=list)  # keys no archetype declares
    organization_name: str = ""

    @property
    def lines(self) -> list[str]:
        out = [f"{row['key']:<26} {row['location_id']}" for row in self.imported]
        out += [f"{key:<26} already imported" for key in self.skipped]
        out += [f"{key:<26} unknown" for key in self.unknown]
        return out


async def existing_keys(db: AsyncSession, organization_id: UUID) -> dict[str, UUID]:
    """Which archetypes this organization already holds, by key."""
    rows = (
        await db.scalars(
            select(Location).where(
                Location.organization_id == organization_id,
                Location.google_location_name.startswith(NAME_PREFIX),
            )
        )
    ).all()
    return {key: row.id for row in rows if (key := key_of(row)) in KEYS}


async def catalogue(db: AsyncSession, organization_id: UUID) -> list[dict]:
    """The ten archetypes, each marked with whether this organization already has it."""
    present = await existing_keys(db, organization_id)
    return [
        {
            "key": a.key,
            "name": a.name,
            "industry": a.industry,
            "city": a.location,
            "headline_problem": a.headline_problem,
            "expected_grade": a.expected_grade,
            "imported": a.key in present,
            "location_id": str(present[a.key]) if a.key in present else None,
        }
        for a in ARCHETYPES
    ]


async def import_archetypes(
    db: AsyncSession,
    organization_id: UUID,
    keys: list[str],
    project_id: UUID | None = None,
    reference: date | None = None,
) -> ImportResult:
    """Write each unseen archetype into the organization. Does not commit, and never audits.

    Unknown keys are reported rather than raised, so one stale key in a batch cannot stop
    the rest from importing. An archetype the organization already has is skipped whole:
    re-importing must never duplicate a profile or double its reviews.
    """
    result = ImportResult()
    present = await existing_keys(db, organization_id)
    seen: set[str] = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        if key not in KEYS:
            result.unknown.append(key)
        elif key in present:
            result.skipped.append(key)
        else:
            data = generate(by_key(key), reference)
            location = await write_profile(db, organization_id, data, project_id)
            result.imported.append({"key": key, "location_id": str(location.id)})
    return result


async def write_profile(
    db: AsyncSession,
    organization_id: UUID,
    data: ProfileData,
    project_id: UUID | None = None,
) -> Location:
    """One generated business: the profile, its project, and every analytics row."""
    location = Location(
        organization_id=organization_id,
        source=LocationSource.fixture,
        open_status=OpenStatus(data.location["open_status"]),
        **{k: v for k, v in data.location.items() if k != "open_status"},
    )
    db.add(location)
    await db.flush()

    await _catalog(db, organization_id, data)
    _profile_rows(db, location, data)
    await _project(db, organization_id, location, data, project_id)
    _reviews(db, organization_id, location, data)
    _analytics(db, organization_id, location, data)
    await _keywords(db, organization_id, location, data)
    await db.flush()
    return location


async def _catalog(db: AsyncSession, organization_id: UUID, data: ProfileData) -> None:
    """The archetype's attribute vocabulary, upserted on its external id."""
    ids = [row["external_attribute_id"] for row in data.catalog]
    existing = set(
        (
            await db.scalars(
                select(AttributeCatalogItem.external_attribute_id).where(
                    AttributeCatalogItem.organization_id == organization_id,
                    AttributeCatalogItem.external_attribute_id.in_(ids),
                )
            )
        ).all()
    )
    for row in data.catalog:
        if row["external_attribute_id"] not in existing:
            db.add(AttributeCatalogItem(organization_id=organization_id, **row))


def _profile_rows(db: AsyncSession, location: Location, data: ProfileData) -> None:
    for row in data.categories:
        db.add(LocationCategory(location_id=location.id, **row))
    for row in data.hours:
        db.add(LocationHoursPeriod(location_id=location.id, **row))
    for row in data.attributes:
        db.add(LocationAttributeValue(location_id=location.id, **row))


async def _project(
    db: AsyncSession,
    organization_id: UUID,
    location: Location,
    data: ProfileData,
    project_id: UUID | None,
) -> None:
    """Attach the profile to a project, so the project-scoped screens can find it.

    The dashboard is project-scoped: a profile that belongs to no project shows up in
    neither the profiles list nor the audit directory. A caller-supplied project wins;
    otherwise the archetype gets its own, carrying its service list for the relevance and
    suggestion checks that read it.
    """
    if project_id is None:
        project = await db.scalar(
            select(Project).where(
                Project.organization_id == organization_id,
                Project.slug == data.project["slug"],
            )
        )
        if project is None:
            project = Project(organization_id=organization_id, **data.project)
            db.add(project)
            await db.flush()
        project_id = project.id

    linked = await db.scalar(
        select(ProjectLocation.id).where(
            ProjectLocation.project_id == project_id,
            ProjectLocation.location_id == location.id,
        )
    )
    if linked is None:
        db.add(ProjectLocation(project_id=project_id, location_id=location.id))


def _reviews(db: AsyncSession, organization_id: UUID, location: Location, data) -> None:
    for row in data.reviews:
        db.add(Review(organization_id=organization_id, location_id=location.id, **row))


def _analytics(db: AsyncSession, organization_id: UUID, location: Location, data) -> None:
    common = {"organization_id": organization_id, "location_id": location.id}
    for row in data.performance:
        db.add(PerformanceDaily(**common, source=DataSource.locus, **row))
    for row in data.search_terms:
        db.add(SearchTermMonthly(**common, source=DataSource.locus, **row))
    if data.media:
        db.add(MediaSummary(**common, source=DataSource.locus, **data.media))
    for row in data.posts:
        db.add(
            Post(
                **common,
                source=DataSource.locus,
                **{
                    **row,
                    "post_type": PostType(row["post_type"]),
                    "cta_type": PostCtaType(row["cta_type"]) if row["cta_type"] else None,
                },
            )
        )
    for row in data.bookings:
        db.add(
            Booking(
                **common,
                source=DataSource.locus,
                **{
                    **row,
                    "status": BookingStatus(row["status"]),
                    "booking_source": (
                        BookingChannel(row["booking_source"]) if row["booking_source"] else None
                    ),
                },
            )
        )


async def _keywords(
    db: AsyncSession, organization_id: UUID, location: Location, data: ProfileData
) -> None:
    common = {"organization_id": organization_id, "location_id": location.id}
    keyword_id: dict[str, UUID] = {}
    for row in data.keywords:
        keyword = TrackedKeyword(
            **common,
            source=DataSource.locus,
            **{**row, "search_intent": SearchIntent(row["search_intent"])},
        )
        db.add(keyword)
        await db.flush()
        keyword_id[row["external_keyword_id"]] = keyword.id

    for row in data.ranks:
        values = {k: v for k, v in row.items() if k != "keyword_ref"}
        db.add(
            KeywordRank(
                **common,
                source=DataSource.locus,
                tracked_keyword_id=keyword_id[row["keyword_ref"]],
                **values,
            )
        )
    for row in data.competitors:
        values = {k: v for k, v in row.items() if k != "keyword_ref"}
        db.add(
            CompetitorObservation(
                organization_id=organization_id,
                source=DataSource.locus,
                tracked_keyword_id=keyword_id[row["keyword_ref"]],
                **values,
            )
        )


# ---- the command line path -----------------------------------------------------------


async def resolve_organization(db: AsyncSession, slug: str | None) -> Organization:
    if slug:
        organization = await db.scalar(select(Organization).where(Organization.slug == slug))
        if organization is None:
            raise LookupError(f"No organization with the slug {slug!r}")
        return organization
    organizations = (await db.scalars(select(Organization).order_by(Organization.created_at))).all()
    if not organizations:
        raise LookupError("No organization exists yet. Run `uv run python -m app.seed` first.")
    return organizations[0]


async def resolve_project(db: AsyncSession, organization_id: UUID, name: str | None):
    if not name:
        return None
    project = await db.scalar(
        select(Project).where(Project.organization_id == organization_id, Project.name == name)
    )
    if project is None:
        raise LookupError(f"No project named {name!r} in this organization")
    return project.id


async def import_into_database(
    db: AsyncSession,
    keys: list[str],
    organization_slug: str | None = None,
    project_name: str | None = None,
    reference: date | None = None,
) -> ImportResult:
    """Resolve the organization, import the archetypes and commit. Used by the CLI."""
    organization = await resolve_organization(db, organization_slug)
    project_id = await resolve_project(db, organization.id, project_name)
    result = await import_archetypes(
        db, organization.id, keys, project_id=project_id, reference=reference
    )
    await db.commit()
    result.organization_name = f"{organization.name} [{organization.slug}]"
    return result


__all__ = [
    "Archetype",
    "ImportResult",
    "catalogue",
    "existing_keys",
    "import_archetypes",
    "import_into_database",
    "location_name",
    "write_profile",
]
