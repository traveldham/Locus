from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.models import ProjectStatus
from app.schemas.locations import LocationSummary

NAME_MIN = 2
NAME_MAX = 160


def clean_name(value: str) -> str:
    name = value.strip()
    if not NAME_MIN <= len(name) <= NAME_MAX:
        raise ValueError(f"Name must be between {NAME_MIN} and {NAME_MAX} characters")
    return name


ProjectName = Annotated[str, AfterValidator(clean_name)]


class BusinessFields(BaseModel):
    website_url: str | None = Field(None, max_length=2083)
    description: str | None = Field(None, max_length=5000)
    services: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("website_url")
    @classmethod
    def validate_website(cls, value):
        if value is None or not value.strip():
            return None
        url = HttpUrl(value.strip())
        if url.username or url.password:
            raise ValueError("Website URL must not include credentials")
        return str(url)

    @field_validator("description")
    @classmethod
    def trim_description(cls, value):
        return value.strip() or None if value is not None else None

    @field_validator("services")
    @classmethod
    def clean_services(cls, values):
        result, seen = [], set()
        for value in values:
            value = value.strip()
            if not 1 <= len(value) <= 120:
                raise ValueError("Each service must be between 1 and 120 characters")
            if value.casefold() not in seen:
                result.append(value)
                seen.add(value.casefold())
        return result


class ProjectCreate(BusinessFields):
    name: ProjectName
    google_connection_id: UUID | None = None
    location_ids: list[UUID] | None = None


class ProjectUpdate(BusinessFields):
    name: ProjectName | None = None
    status: ProjectStatus | None = None


class ProjectLocationsRequest(BaseModel):
    location_ids: list[UUID]


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    website_url: str | None = None
    description: str | None = None
    services: list[str] = Field(default_factory=list)
    slug: str
    status: ProjectStatus
    location_count: int = 0
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    model_config = ConfigDict(from_attributes=True)

    google_connection_id: UUID | None = None
    locations: list[LocationSummary] = []
