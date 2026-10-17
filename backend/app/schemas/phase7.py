"""Pydantic schemas for Phase 7: StudentNeed, HelperMatch, LegacyHandover,
EventMemory, and FollowUpTask.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# StudentNeed schemas
# ---------------------------------------------------------------------------


class StudentNeedCreate(BaseModel):
    """Payload for declaring a new student need."""

    title: str = Field(min_length=3, max_length=255)
    category: str = Field(
        min_length=2,
        max_length=64,
        description=(
            "Category aligned with HelpOffer categories (e.g. mock_interview, portfolio_review)."
        ),
    )
    description: str | None = Field(
        default=None,
        description="Optional detail about what specifically the student needs help with.",
    )
    preferred_delivery_mode: str | None = Field(
        default=None,
        description="Preferred mode: remote, in_person, hybrid, or async.",
    )
    urgency: str = Field(
        default="medium",
        description="Self-reported urgency: low, medium, or high.",
    )
    extra_data: dict[str, Any] | None = None


class StudentNeedUpdate(BaseModel):
    """Payload for updating an existing student need (must be OPEN)."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    description: str | None = None
    preferred_delivery_mode: str | None = None
    urgency: str | None = None
    status: str | None = Field(
        default=None,
        description="Allowed transitions: resolved, withdrawn.",
    )
    extra_data: dict[str, Any] | None = None


class StudentNeedRead(BaseModel):
    """Read contract for a StudentNeed."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: str
    institution_id: str
    title: str
    category: str
    description: str | None = None
    preferred_delivery_mode: str | None = None
    urgency: str
    status: str
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class StudentNeedListResponse(BaseModel):
    items: list[StudentNeedRead]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# HelperMatch schemas
# ---------------------------------------------------------------------------


class RuleResult(BaseModel):
    """Single rule evaluation result inside a HelperMatch."""

    rule: str
    matched: bool | None
    weight: float
    contribution: float
    evidence: str


class HelperMatchRead(BaseModel):
    """Read contract for a HelperMatch, including full rule transparency."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    need_id: str
    help_offer_id: str
    institution_id: str
    score: float
    rule_results: list[dict[str, Any]]
    summary_explanation: str | None = None
    uncertainty_notes: str | None = None
    scorer_version: str
    is_seen: bool
    status: str
    created_at: datetime
    updated_at: datetime
    # Denormalised offer context for display
    offer_title: str | None = None
    offer_category: str | None = None
    offer_delivery_mode: str | None = None
    offer_owner_name: str | None = None


class HelperMatchUpdateStatus(BaseModel):
    """Payload for student to update a match status (accepted or dismissed)."""

    status: str = Field(description="'accepted' or 'dismissed'")


class HelperMatchListResponse(BaseModel):
    items: list[HelperMatchRead]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# LegacyHandover schemas
# ---------------------------------------------------------------------------


class KeyContact(BaseModel):
    """A named contact entry in a handover document."""

    name: str
    role: str | None = None
    email: str | None = None
    notes: str | None = None


class LegacyHandoverCreate(BaseModel):
    """Payload for creating a new DRAFT handover."""

    title: str = Field(min_length=3, max_length=255)
    position_id: str | None = None
    incoming_user_id: str | None = None
    accomplishments_summary: str | None = None
    ongoing_work: str | None = None
    key_contacts: list[KeyContact] = Field(default_factory=list)
    lessons_learned: str | None = None
    recommended_first_steps: str | None = None


class LegacyHandoverUpdate(BaseModel):
    """Payload for updating a DRAFT handover."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    incoming_user_id: str | None = None
    accomplishments_summary: str | None = None
    ongoing_work: str | None = None
    key_contacts: list[KeyContact] | None = None
    lessons_learned: str | None = None
    recommended_first_steps: str | None = None


class LegacyHandoverRead(BaseModel):
    """Read contract for a LegacyHandover."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    position_id: str | None = None
    outgoing_user_id: str
    incoming_user_id: str | None = None
    title: str
    accomplishments_summary: str | None = None
    ongoing_work: str | None = None
    key_contacts: list[dict[str, Any]]
    lessons_learned: str | None = None
    recommended_first_steps: str | None = None
    version: int
    status: str
    acknowledged_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    # Denormalised context
    position_title: str | None = None
    outgoing_user_name: str | None = None
    incoming_user_name: str | None = None


class LegacyHandoverListResponse(BaseModel):
    items: list[LegacyHandoverRead]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# EventMemory schemas
# ---------------------------------------------------------------------------


class EventMemoryCreate(BaseModel):
    """Payload for creating an institutional event memory record."""

    title: str = Field(min_length=3, max_length=255)
    opportunity_id: str | None = None
    handover_id: str | None = None
    what_worked: str | None = None
    what_did_not_work: str | None = None
    attendance_notes: str | None = None
    outcome_summary: str | None = None
    context_notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra_data: dict[str, Any] | None = None


class EventMemoryUpdate(BaseModel):
    """Payload for amending an event memory (creates a new version)."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    what_worked: str | None = None
    what_did_not_work: str | None = None
    attendance_notes: str | None = None
    outcome_summary: str | None = None
    context_notes: str | None = None
    tags: list[str] | None = None
    extra_data: dict[str, Any] | None = None


class EventMemoryRead(BaseModel):
    """Read contract for an EventMemory record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    opportunity_id: str | None = None
    handover_id: str | None = None
    author_user_id: str
    title: str
    what_worked: str | None = None
    what_did_not_work: str | None = None
    attendance_notes: str | None = None
    outcome_summary: str | None = None
    context_notes: str | None = None
    tags: list[str]
    superseded_by_id: str | None = None
    is_current: bool
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    author_name: str | None = None
    opportunity_title: str | None = None


class EventMemoryListResponse(BaseModel):
    items: list[EventMemoryRead]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# FollowUpTask schemas
# ---------------------------------------------------------------------------


class FollowUpTaskCreate(BaseModel):
    """Payload for creating an actionable follow-up task."""

    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    assignee_user_id: str
    handover_id: str | None = None
    match_id: str | None = None
    due_date: datetime | None = None
    priority: str = Field(default="medium", description="low, medium, or high")
    extra_data: dict[str, Any] | None = None


class FollowUpTaskUpdate(BaseModel):
    """Payload for updating a task."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    assignee_user_id: str | None = None
    due_date: datetime | None = None
    priority: str | None = None
    is_completed: bool | None = None
    extra_data: dict[str, Any] | None = None


class FollowUpTaskRead(BaseModel):
    """Read contract for a FollowUpTask."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    source: str
    handover_id: str | None = None
    match_id: str | None = None
    title: str
    description: str | None = None
    assignee_user_id: str
    creator_user_id: str
    due_date: datetime | None = None
    priority: str
    is_completed: bool
    completed_at: datetime | None = None
    extra_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    assignee_name: str | None = None
    creator_name: str | None = None


class FollowUpTaskListResponse(BaseModel):
    items: list[FollowUpTaskRead]
    total: int
    limit: int
    offset: int
