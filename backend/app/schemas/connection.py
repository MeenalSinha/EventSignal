"""Schema for ConnectionRequest.

Connection requests may only be sent to alumni profiles that have explicitly
declared willingness to connect (``willing_to_connect = True``). This validation
is enforced at the API layer, not in the Pydantic schema alone.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.connection_request import ConnectionPurpose, RequestStatus


class ConnectionRequestCreate(BaseModel):
    """Input schema for creating a connection request."""

    requester_profile_id: str = Field(min_length=1)
    recipient_profile_id: str = Field(min_length=1)
    purpose: ConnectionPurpose
    # Message is optional but required when purpose is OTHER.
    message: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _message_required_for_other(self) -> ConnectionRequestCreate:
        if self.purpose is ConnectionPurpose.OTHER and not self.message:
            raise ValueError("A message explaining the purpose is required when purpose is 'other'")
        return self

    @model_validator(mode="after")
    def _cannot_connect_to_self(self) -> ConnectionRequestCreate:
        if self.requester_profile_id == self.recipient_profile_id:
            raise ValueError("A student cannot send a connection request to themselves")
        return self


class ConnectionRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requester_profile_id: str
    recipient_profile_id: str
    purpose: ConnectionPurpose
    message: str | None
    status: RequestStatus
    responded_at: datetime | None
    created_at: datetime
    updated_at: datetime
