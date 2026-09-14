import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agent import router as agent_router
from app.api.auth import router as auth_router
from app.api.bookings import router as bookings_router
from app.api.health import router as health_router
from app.api.insights import router as insights_router
from app.api.integrations import router as integrations_router
from app.api.locations import router as locations_router
from app.api.market import router as market_router
from app.api.posts import router as posts_router
from app.api.projects import router as projects_router
from app.api.recommendations import router as recommendations_router
from app.api.reviews import router as reviews_router
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Populate the demo world on first boot so the app is never shown empty.

    Imported lazily: `app.seed` pulls in the sample CSV readers, which the test suite
    neither needs nor should pay for at import time.
    """
    from app.core.database import SessionLocal
    from app.seed import seed_if_empty

    try:
        async with SessionLocal() as db:
            summary = await seed_if_empty(db)
    except Exception:
        # A failed seed must not stop the API from serving — the empty state explains itself.
        logger.exception("Demo seeding failed; starting with whatever is already in the database")
    else:
        if summary is None:
            logger.info("Demo data already present; skipping seed")
        else:
            logger.info("Seeded the demo world:\n  %s", "\n  ".join(summary))
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in (
    health_router,
    auth_router,
    integrations_router,
    projects_router,
    posts_router,
    locations_router,
    reviews_router,
    recommendations_router,
    insights_router,
    market_router,
    bookings_router,
    agent_router,
):
    app.include_router(router, prefix=settings.api_prefix)


@app.exception_handler(Exception)
async def unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
    if settings.app_env == "development":
        return JSONResponse(status_code=500, content={"detail": str(exc)})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
