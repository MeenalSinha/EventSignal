"""Schema for ConnectionRequest and HelpOffer requests.

Connection requests may only be sent to alumni profiles or published help offers
that have explicitly declared willingness to connect / help.
This validation is enforced at the API layer, not in the Pydantic schema alone.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.connection_request import ConnectionPurpose, RequestStatus


class ConnectionRequestCreate(BaseModel):
    """Input schema for creating a connection request."""

    requester_profile_id: str = Field(min_length=1)
    recipient_profile_id: str = Field(min_length=1)
    help_offer_id: str | None = None
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
            raise ValueError("A member cannot send a connection request to themselves")
        return self


class HelpOfferRequestCreate(BaseModel):
    """Payload for requesting assistance on a published help offer."""

    purpose: ConnectionPurpose = ConnectionPurpose.SKILL_MENTORING
    message: str | None = Field(default=None, max_length=2000)


class ConnectionRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requester_profile_id: str
    recipient_profile_id: str
    help_offer_id: str | None = None
    purpose: ConnectionPurpose
    message: str | None
    status: RequestStatus
    responded_at: datetime | None
    created_at: datetime
    updated_at: datetime
