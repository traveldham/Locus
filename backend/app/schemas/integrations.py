from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import ConnectionStatus


class ConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    google_account_email: str
    status: ConnectionStatus
    scopes: list[str]
    connected_at: datetime
    last_synced_at: datetime | None = None
