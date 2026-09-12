import re
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    digest_token,
    hash_password,
    new_refresh_token,
    verify_password,
)
from app.models import MembershipRole, Organization, OrganizationMembership, RefreshSession, User
from app.schemas import (
    LoginRequest,
    MessageResponse,
    OrganizationSummary,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
REFRESH_COOKIE = "locus_refresh"


def is_expired(expires_at: datetime, now: datetime) -> bool:
    """Compare timestamps safely, including SQLite's timezone-naive test values."""
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at < now


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        organizations=[
            OrganizationSummary(
                id=item.organization.id,
                name=item.organization.name,
                slug=item.organization.slug,
                role=item.role,
            )
            for item in user.memberships
        ],
    )


async def loaded_user(db: DbSession, user_id) -> User:
    result = await db.execute(
        select(User)
        .options(selectinload(User.memberships).selectinload(OrganizationMembership.organization))
        .where(User.id == user_id)
    )
    return result.scalar_one()


def set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=f"{settings.api_prefix}/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        REFRESH_COOKIE,
        path=f"{settings.api_prefix}/auth",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )


async def issue_session(db: DbSession, response: Response, user: User) -> TokenResponse:
    settings = get_settings()
    refresh = new_refresh_token()
    db.add(
        RefreshSession(
            user_id=user.id,
            token_digest=digest_token(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    await db.commit()
    set_refresh_cookie(response, refresh)
    access, expires_in = create_access_token(user.id)
    user = await loaded_user(db, user.id)
    return TokenResponse(access_token=access, expires_in=expires_in, user=serialize_user(user))


async def unique_slug(db: DbSession, name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "organization"
    candidate = base
    number = 2
    while await db.scalar(select(Organization.id).where(Organization.slug == candidate)):
        candidate = f"{base}-{number}"
        number += 1
    return candidate


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, response: Response, db: DbSession) -> TokenResponse:
    email = payload.email.lower().strip()
    if await db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    organization = Organization(
        name=payload.organization_name,
        slug=await unique_slug(db, payload.organization_name),
    )
    try:
        db.add_all([user, organization])
        await db.flush()
        db.add(
            OrganizationMembership(
                user_id=user.id, organization_id=organization.id, role=MembershipRole.owner
            )
        )
        return await issue_session(db, response, user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account or organization with these details already exists",
        ) from None


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, db: DbSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email.lower().strip()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    return await issue_session(db, response, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: DbSession) -> TokenResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Refresh session required")
    result = await db.execute(
        select(RefreshSession)
        .where(RefreshSession.token_digest == digest_token(raw_token))
        .with_for_update()
    )
    session = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if session is None or session.revoked_at is not None or is_expired(session.expires_at, now):
        raise HTTPException(status_code=401, detail="Refresh session is invalid or expired")
    user = await db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Refresh session is invalid")
    session.revoked_at = now
    await db.flush()
    return await issue_session(db, response, user)


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response, db: DbSession) -> MessageResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if raw_token:
        result = await db.execute(
            select(RefreshSession).where(RefreshSession.token_digest == digest_token(raw_token))
        )
        session = result.scalar_one_or_none()
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(UTC)
            await db.commit()
    clear_refresh_cookie(response)
    return MessageResponse(message="Signed out")


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser, db: DbSession) -> UserResponse:
    return serialize_user(await loaded_user(db, current_user.id))
