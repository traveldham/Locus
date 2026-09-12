"""Local-search ranking data.

Nothing in this module comes from Google, and nothing in it ever can: there is no
ranking API, Google never discloses a competitor's profile, and the tracked keyword list
is our own configuration. Every row here is written with `source = locus` so the product
can say so on screen instead of letting a user assume it came from their Google
dashboard and then wonder why the numbers never reconcile.
"""

from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, DataSource, TimestampMixin


class SearchIntent(StrEnum):
    general = "general"
    emergency = "emergency"
    cosmetic = "cosmetic"
    pediatric = "pediatric"
    implants = "implants"
    orthodontics = "orthodontics"
    insurance = "insurance"


class TrackedKeyword(TimestampMixin, Base):
    """A local-search keyword we watch on a location's behalf."""

    __tablename__ = "tracked_keywords"
    __table_args__ = (UniqueConstraint("location_id", "external_keyword_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )

    # The rank provider's own id for this keyword; the join key in every feed they send.
    external_keyword_id: Mapped[str] = mapped_column(String(64))
    keyword: Mapped[str] = mapped_column(String(512))
    search_intent: Mapped[SearchIntent | None] = mapped_column(
        Enum(SearchIntent, name="search_intent"), nullable=True
    )
    # "mobile" / "desktop" as the provider labels it — free text rather than an enum,
    # because the device list is theirs to extend and a new value must not fail the load.
    device: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tracking_started_on: Mapped[date | None] = mapped_column(Date, nullable=True)

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.locus
    )

    ranks: Mapped[list["KeywordRank"]] = relationship(
        back_populates="tracked_keyword", cascade="all, delete-orphan"
    )
    competitor_observations: Mapped[list["CompetitorObservation"]] = relationship(
        back_populates="tracked_keyword", cascade="all, delete-orphan"
    )


class KeywordRank(TimestampMixin, Base):
    """One weekly rank check for one tracked keyword."""

    __tablename__ = "keyword_ranks"
    __table_args__ = (UniqueConstraint("tracked_keyword_id", "week_start"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    tracked_keyword_id: Mapped[UUID] = mapped_column(
        ForeignKey("tracked_keywords.id", ondelete="CASCADE")
    )

    # Weeks start Monday.
    week_start: Mapped[date] = mapped_column(Date)
    # NULL means the location was not found in the checked results — not rank 0, and not
    # "worst possible". Averaging over these rows must skip them, not coerce them.
    rank_absolute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 1-3 when the location made the three-result local pack, NULL when it did not.
    rank_in_local_pack: Mapped[int | None] = mapped_column(Integer, nullable=True)
    found: Mapped[bool] = mapped_column(Boolean, default=False)
    result_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.locus
    )

    tracked_keyword: Mapped[TrackedKeyword] = relationship(back_populates="ranks")


class CompetitorObservation(TimestampMixin, Base):
    """A rival business seen ranking on one keyword in one week.

    Hangs off the keyword rather than the location: a competitor is only ever observed
    *in the context of a query*, and the same business shows up for several keywords.
    There is deliberately no unique constraint — a keyword-week holds several
    competitors, which is the whole point of the row.
    """

    __tablename__ = "competitor_observations"
    __table_args__ = (
        Index(
            "ix_competitor_observations_tracked_keyword_id_week_start",
            "tracked_keyword_id",
            "week_start",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    tracked_keyword_id: Mapped[UUID] = mapped_column(
        ForeignKey("tracked_keywords.id", ondelete="CASCADE")
    )

    week_start: Mapped[date] = mapped_column(Date)
    competitor_name: Mapped[str] = mapped_column(String(320))
    # Stable per business, so the same rival can be followed across keywords and weeks.
    competitor_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    rank_absolute: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # The competitor's profile as observed that week — a snapshot, not a live figure.
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    photo_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_claimed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    source: Mapped[DataSource] = mapped_column(
        Enum(DataSource, name="data_source"), default=DataSource.locus
    )

    tracked_keyword: Mapped[TrackedKeyword] = relationship(back_populates="competitor_observations")
