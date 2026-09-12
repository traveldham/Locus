import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(user_id: UUID) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.access_token_minutes)
    token = jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "jti": secrets.token_urlsafe(16),
            "iat": now,
            "exp": expires,
        },
        settings.secret_key,
        algorithm="HS256",
    )
    return token, int((expires - now).total_seconds())


def decode_access_token(token: str) -> UUID:
    payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return UUID(payload["sub"])


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
