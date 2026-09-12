from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ConnectionStatus(StrEnum):
    active = "active"
    needs_reauth = "needs_reauth"
    revoked = "revoked"
    error = "error"


class GoogleConnection(TimestampMixin, Base):
    """An organization's Google Business Profile connection (business.manage).

    Written once by `app.seed` and only ever read back, so the UI can show the
    integration as connected.
    """

    __tablename__ = "google_connections"
    __table_args__ = (UniqueConstraint("organization_id", "google_subject"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    google_account_email: Mapped[str] = mapped_column(String(320))
    google_subject: Mapped[str] = mapped_column(String(255))
    # Nothing in the application calls Google, so the seed stores an obvious placeholder
    # here rather than a credential.
    refresh_token_encrypted: Mapped[str] = mapped_column(Text)
    scopes: Mapped[str] = mapped_column(Text)
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus, name="connection_status"), default=ConnectionStatus.active
    )
    connected_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    accounts: Mapped[list["ExternalAccount"]] = relationship(
        back_populates="connection", cascade="all, delete-orphan"
    )


class ExternalAccount(TimestampMixin, Base):
    """A Google Business Profile account (`accounts/123456`) reachable via a connection."""

    __tablename__ = "external_accounts"
    __table_args__ = (UniqueConstraint("connection_id", "resource_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("google_connections.id", ondelete="CASCADE"), index=True
    )
    resource_name: Mapped[str] = mapped_column(String(255))
    account_name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verification_state: Mapped[str | None] = mapped_column(String(64), nullable=True)

    connection: Mapped[GoogleConnection] = relationship(back_populates="accounts")
