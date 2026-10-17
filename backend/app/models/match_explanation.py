"""MatchExplanation: records why a particular opportunity or person was recommended.

Every match explanation must be grounded in actual profile attributes. The system
must not invent reasons, fabricate qualifications, or assert that a recommendation
is definitively correct.

Explanations reference the scoring version (``scorer_version``) so that changes
to matching logic can be detected and old explanations can be recomputed or invalidated.

Migration note: introduced in Alembic revision 0001.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_id


class MatchedEntityType(enum.StrEnum):
    """What kind of entity was matched."""

    OPPORTUNITY = "opportunity"
    ALUMNI = "alumni"


class MatchExplanation(TimestampMixin, Base):
    __tablename__ = "match_explanations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # The student profile for whom the match was computed.
    student_profile_id: Mapped[str] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # The matched entity — either an opportunity or an alumni profile.
    matched_entity_type: Mapped[MatchedEntityType] = mapped_column(
        Enum(
            MatchedEntityType,
            native_enum=False,
            length=24,
            create_constraint=True,
            name="matched_entity_type",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
    )
    matched_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Numeric relevance score from the matching rule engine.
    # This is a system-computed value, not a guarantee of suitability.
    score: Mapped[float | None] = mapped_column()

    # Human-readable reasons, each grounded in an actual profile attribute.
    # Must not contain fabricated explanations.
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # Profile attributes that contributed to the match — for auditability.
    contributing_attributes: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Uncertainty or limitations of this recommendation.
    uncertainty_notes: Mapped[str | None] = mapped_column(Text)

    # The version identifier of the matching rules used.
    scorer_version: Mapped[str] = mapped_column(String(50), nullable=False)
