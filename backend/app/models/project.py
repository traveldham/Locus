from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, utcnow
from app.models.location import Location


class ProjectStatus(StrEnum):
    active = "active"
    archived = "archived"


class Project(TimestampMixin, Base):
    """A named folder of locations. One connection can feed many projects."""

    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "slug"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    website_url: Mapped[str | None] = mapped_column(String(2083), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    services: Mapped[list[str]] = mapped_column(JSON, default=list)
    slug: Mapped[str] = mapped_column(String(100))
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"), default=ProjectStatus.active
    )
    google_connection_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("google_connections.id", ondelete="SET NULL"), nullable=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    project_locations: Mapped[list["ProjectLocation"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectLocation(Base):
    """Many-to-many join: a location may belong to several projects."""

    __tablename__ = "project_locations"
    __table_args__ = (UniqueConstraint("project_id", "location_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project] = relationship(back_populates="project_locations")
    location: Mapped[Location] = relationship()
