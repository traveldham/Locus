"""Build the demo world: one account, one organization, and the whole sample dataset.

    uv run python -m app.seed

Locus Intelligence ships a single pre-seeded demo account. There is no registration and
no live Google connection — Google never approved this Cloud project for Business Profile
API access, so the `GoogleConnection` row written here exists purely so the UI can show
the integration as connected, and its refresh-token column holds an obvious placeholder
rather than a secret.

Every write is an upsert keyed on a natural identifier, so running this repeatedly
refreshes the demo world instead of duplicating it.
"""

from __future__ import annotations

import asyncio
import re
import sys
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    ConnectionStatus,
    GoogleConnection,
    Location,
    MembershipRole,
    Organization,
    OrganizationMembership,
    Project,
    ProjectLocation,
    Review,
    User,
    utcnow,
)
from app.sample_business import populate_business
from app.services.gbp_sync import (
    link_locations_to_project,
    upsert_external_accounts,
    upsert_location,
)
from app.services.providers import ProviderError
from app.services.providers.reviews import SampleReviewsProvider
from app.services.providers.sample import SampleGbpProvider
from app.services.providers.sample_data import SAMPLE_ACCOUNT, data_dir
from app.services.sample_datasets import SampleDataError, load_sample_datasets

DEMO_EMAIL = "pawanpatrapp@gmail.com"
DEMO_PASSWORD = "Pawan 2000"
DEMO_FULL_NAME = "Pawan Patra"
ORGANIZATION_NAME = "Brightpath Dental Group"
# The demo project carries the business name, so the workspace reads as that company
# rather than a generic bucket.
PROJECT_NAME = ORGANIZATION_NAME

# The scope a real Business Profile grant would carry. Recorded so the integration screen
# can show what the connection covers; nothing reads it to make a call.
BUSINESS_PROFILE_SCOPE = "https://www.googleapis.com/auth/business.manage"

# The connection's Google identity. `google_subject` is what makes the row unique per
# organization, so a re-run finds this one instead of adding another.
GOOGLE_SUBJECT = "demo-connection"
# `refresh_token_encrypted` is NOT NULL and nothing ever calls Google, so this is a
# deliberately non-secret placeholder rather than a credential.
REFRESH_TOKEN_PLACEHOLDER = "demo-connection"


def slugify(value: str, fallback: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or fallback


async def seed_user(db: AsyncSession) -> User:
    user = await db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        user = User(email=DEMO_EMAIL)
        db.add(user)
    user.full_name = DEMO_FULL_NAME
    user.password_hash = hash_password(DEMO_PASSWORD)
    user.is_active = True
    await db.flush()
    return user


async def seed_organization(db: AsyncSession, user: User) -> Organization:
    slug = slugify(ORGANIZATION_NAME, "organization")
    organization = await db.scalar(select(Organization).where(Organization.slug == slug))
    if organization is None:
        organization = Organization(name=ORGANIZATION_NAME, slug=slug)
        db.add(organization)
    organization.name = ORGANIZATION_NAME
    await db.flush()

    membership = await db.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == organization.id,
        )
    )
    if membership is None:
        membership = OrganizationMembership(user_id=user.id, organization_id=organization.id)
        db.add(membership)
    membership.role = MembershipRole.owner
    await db.flush()
    return organization


async def seed_connection(
    db: AsyncSession, organization: Organization, user: User
) -> GoogleConnection:
    connection = await db.scalar(
        select(GoogleConnection).where(
            GoogleConnection.organization_id == organization.id,
            GoogleConnection.google_subject == GOOGLE_SUBJECT,
        )
    )
    if connection is None:
        connection = GoogleConnection(
            organization_id=organization.id, google_subject=GOOGLE_SUBJECT
        )
        db.add(connection)
    connection.google_account_email = DEMO_EMAIL
    connection.refresh_token_encrypted = REFRESH_TOKEN_PLACEHOLDER
    connection.scopes = BUSINESS_PROFILE_SCOPE
    connection.status = ConnectionStatus.active
    connection.connected_by_user_id = user.id
    connection.last_error = None
    connection.last_synced_at = utcnow()
    await db.flush()
    return connection


async def seed_locations(
    db: AsyncSession, organization: Organization, connection: GoogleConnection
) -> list[Location]:
    """Every sample location, with its hours, categories and attributes."""
    provider = SampleGbpProvider()
    accounts = await provider.list_accounts(connection)
    stored_accounts = await upsert_external_accounts(db, connection, accounts)
    external_account_id = {row.resource_name: row.id for row in stored_accounts}

    synced_at = utcnow()
    return [
        await upsert_location(
            db,
            organization_id=organization.id,
            connection=connection,
            external_account_id=external_account_id[SAMPLE_ACCOUNT.resource_name],
            payload=payload,
            source=provider.location_source,
            synced_at=synced_at,
        )
        for payload in await provider.list_locations(connection, SAMPLE_ACCOUNT.resource_name)
    ]


async def seed_project(
    db: AsyncSession,
    organization: Organization,
    connection: GoogleConnection,
    user: User,
    locations: list[Location],
) -> Project:
    project = await db.scalar(
        select(Project).where(
            Project.organization_id == organization.id, Project.name == PROJECT_NAME
        )
    )
    if project is None:
        project = Project(
            organization_id=organization.id,
            name=PROJECT_NAME,
            slug=slugify(PROJECT_NAME, "project"),
            created_by_user_id=user.id,
        )
        db.add(project)
        await db.flush()
    project.google_connection_id = connection.id
    populate_business(project)
    await link_locations_to_project(db, project, locations)
    return project


async def seed_reviews(
    db: AsyncSession,
    organization_id: UUID,
    connection: GoogleConnection,
    locations: list[Location],
) -> tuple[int, int]:
    """Every sample review with its owner reply. Returns (reviews, replies)."""
    provider = SampleReviewsProvider()
    total = replies = 0

    for location in locations:
        fetched = await provider.list_reviews(connection, location)
        existing_rows = await db.execute(select(Review).where(Review.location_id == location.id))
        existing = {row.google_review_id: row for row in existing_rows.scalars()}

        for payload in fetched:
            review = existing.get(payload.google_review_id)
            if review is None:
                review = Review(
                    organization_id=organization_id,
                    location_id=location.id,
                    google_review_id=payload.google_review_id,
                )
                db.add(review)
            review.google_review_name = payload.google_review_name
            review.reviewer_display_name = payload.reviewer_display_name
            review.reviewer_photo_url = payload.reviewer_photo_url
            review.is_anonymous = payload.is_anonymous
            review.star_rating = payload.star_rating
            review.comment = payload.comment
            review.create_time = payload.create_time
            review.update_time = payload.update_time
            review.reply_comment = payload.reply_comment
            review.reply_update_time = payload.reply_update_time
            total += 1
            replies += bool(payload.reply_comment)
        await db.flush()
    return total, replies


async def seed(db: AsyncSession) -> list[str]:
    """Write the whole demo world in one transaction. Returns the summary lines."""
    user = await seed_user(db)
    organization = await seed_organization(db, user)
    connection = await seed_connection(db, organization, user)
    locations = await seed_locations(db, organization, connection)
    project = await seed_project(db, organization, connection, user, locations)
    reviews, replies = await seed_reviews(db, organization.id, connection, locations)
    datasets = await load_sample_datasets(db, organization.id)
    await db.commit()

    linked = await db.scalar(
        select(func.count(ProjectLocation.id)).where(ProjectLocation.project_id == project.id)
    )
    lines = [
        f"user                      {user.email} ({DEMO_FULL_NAME})",
        f"organization              {organization.name} [{organization.slug}]",
        f"google connection         {connection.google_account_email} ({connection.status.value})",
        f"external accounts         1 ({SAMPLE_ACCOUNT.resource_name})",
        f"locations                 {len(locations)}",
        f"project                   {project.name} [{project.slug}] with {linked or 0} locations",
        f"reviews                   {reviews} ({replies} with an owner reply)",
    ]
    lines.extend(f"{name:<25} {count}" for name, count in datasets.counts.items())
    lines.append(f"{'sample dataset rows':<25} {datasets.total}")
    return lines


async def is_seeded(db: AsyncSession) -> bool:
    """Has the demo world already been written? Keyed on the one account that must exist."""
    return await db.scalar(select(User.id).where(User.email == DEMO_EMAIL)) is not None


async def seed_if_empty(db: AsyncSession) -> list[str] | None:
    """Seed on first run, skip on every run after. Returns the summary, or None if skipped.

    `seed()` is idempotent, but it rewrites ~10k rows; this check keeps a normal restart
    fast. Raises on a genuine failure rather than leaving the app half-populated.
    """
    if await is_seeded(db):
        return None
    if not data_dir().is_dir():
        raise SampleDataError(
            f"The sample CSV directory does not exist: {data_dir()}. "
            "Set SAMPLE_DATA_DIR to the directory holding the sample CSVs."
        )
    return await seed(db)


async def main() -> int:
    directory = data_dir()
    if not directory.is_dir():
        print(
            f"The sample CSV directory does not exist: {directory}\n"
            "The demo world is built entirely from those files. Check out the dataset "
            "beside the backend, or point SAMPLE_DATA_DIR at the directory holding the "
            "sample CSVs, then run this again.",
            file=sys.stderr,
        )
        return 1

    try:
        async with SessionLocal() as db:
            lines = await seed(db)
    except (ProviderError, SampleDataError) as exc:
        print(f"Seeding failed: {exc}", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()

    print(f"Seeded the Locus Intelligence demo world from {directory}\n")
    for line in lines:
        print(f"  {line}")
    print(f"\nSign in as {DEMO_EMAIL} with the password {DEMO_PASSWORD!r}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
