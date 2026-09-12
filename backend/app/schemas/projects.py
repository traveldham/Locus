from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict

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


class ProjectCreate(BaseModel):
    name: ProjectName
    google_connection_id: UUID | None = None
    location_ids: list[UUID] | None = None


class ProjectUpdate(BaseModel):
    name: ProjectName | None = None
    status: ProjectStatus | None = None


class ProjectLocationsRequest(BaseModel):
    location_ids: list[UUID]


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    status: ProjectStatus
    location_count: int = 0
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    model_config = ConfigDict(from_attributes=True)

    google_connection_id: UUID | None = None
    locations: list[LocationSummary] = []
