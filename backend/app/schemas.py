from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import MembershipRole


class OrganizationSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    role: MembershipRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    organizations: list[OrganizationSummary]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    organization_name: str = Field(min_length=2, max_length=160)

    @field_validator("full_name", "organization_name")
    @classmethod
    def validate_nonempty_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("must contain at least 2 non-whitespace characters")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
