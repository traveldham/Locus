import re
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.locations import router as locations_router
from app.api.projects import router as projects_router
from app.api.reviews import router as reviews_router
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import (
    ConnectionStatus,
    GoogleConnection,
    MembershipRole,
    Organization,
    OrganizationMembership,
    User,
)
from stubs import StubGbpProvider, StubReviewsProvider

SessionFactory = async_sessionmaker[AsyncSession]

PASSWORD = "correct-horse-battery-staple"
BUSINESS_PROFILE_SCOPE = "https://www.googleapis.com/auth/business.manage"


def register_router(router: APIRouter) -> None:
    """Mount a router for tests unless app.main already registered it."""
    prefix = get_settings().api_prefix
    mounted = {getattr(route, "path", None) for route in app.routes}
    if f"{prefix}{router.prefix}" not in mounted:
        app.include_router(router, prefix=prefix)


register_router(projects_router)
register_router(locations_router)
register_router(reviews_router)


@pytest.fixture(autouse=True)
def stub_providers(monkeypatch: pytest.MonkeyPatch) -> Iterator[StubReviewsProvider]:
    """Serve every provider read and write from the in-memory stubs in `tests/stubs.py`.

    The application's own provider reads the sample CSVs, whose contents are asserted
    exactly in `test_sample_provider.py`. Every endpoint test runs against the small
    hand-written stub dataset instead, so an API assertion never depends on a CSV. A
    fresh pair of stubs per test also means reply state cannot leak between tests.
    """
    provider = StubGbpProvider()
    reviews = StubReviewsProvider()
    monkeypatch.setattr("app.api.locations.get_provider", lambda: provider)
    monkeypatch.setattr("app.api.reviews.get_reviews_provider", lambda: reviews)
    yield reviews


@pytest_asyncio.fixture
async def session_factory(tmp_path) -> AsyncIterator[SessionFactory]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


@pytest.fixture
def connect_google(session_factory: SessionFactory) -> Callable[[UUID], Awaitable[UUID]]:
    """Give an organization the seeded Google connection every Google-backed endpoint wants."""

    async def _connect(organization_id: UUID) -> UUID:
        async with session_factory() as session:
            connection = GoogleConnection(
                organization_id=organization_id,
                google_account_email="owner@example.com",
                google_subject=f"demo-connection:{organization_id}",
                # Never a credential: nothing in the application calls Google.
                refresh_token_encrypted="demo-connection",
                scopes=BUSINESS_PROFILE_SCOPE,
                status=ConnectionStatus.active,
            )
            session.add(connection)
            await session.commit()
            return connection.id

    return _connect


async def sign_in(
    client: AsyncClient,
    email: str = "owner@example.com",
    organization: str = "Northstar Dental",
    full_name: str = "Locus Owner",
) -> tuple[dict[str, str], UUID]:
    """Seed one account the way `app.seed` does, then log in through the real endpoint.

    Registration no longer exists — the application ships a single pre-seeded account —
    so the suite writes its own accounts and exercises `POST /auth/login` for the token.
    """
    async for session in app.dependency_overrides[get_db]():
        user = User(email=email.lower(), full_name=full_name, password_hash=hash_password(PASSWORD))
        organization_row = Organization(
            name=organization,
            slug=re.sub(r"[^a-z0-9]+", "-", organization.lower()).strip("-"),
        )
        session.add_all([user, organization_row])
        await session.flush()
        session.add(
            OrganizationMembership(
                user_id=user.id,
                organization_id=organization_row.id,
                role=MembershipRole.owner,
            )
        )
        await session.commit()
        organization_id = organization_row.id
        break

    prefix = get_settings().api_prefix
    response = await client.post(
        f"{prefix}/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, organization_id


@pytest_asyncio.fixture
async def client(session_factory: SessionFactory) -> AsyncIterator[AsyncClient]:
    async def override_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
