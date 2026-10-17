"""HelperMatch: a rule-evaluated match between a StudentNeed and a HelpOffer.

Matches are computed by the matching engine.  Every match must be grounded in
actual need and offer attributes.  The engine must not fabricate relevance,
invent qualifications, or assert suitability guarantees.

Explanations are rule-derived.  Each rule that contributed to the score is
recorded in ``rule_results`` as an ordered list of dicts:

    {
        "rule": "category_alignment",
        "matched": true,
        "weight": 0.40,
        "contribution": 0.40,
        "evidence": "Need category 'mock_interview' matches offer category 'mock_interview'"
    }

The final ``score`` is the sum of contributions, normalised to [0, 1].

Migration note: introduced in Alembic revision 0006.
"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_id


class MatchStatus(enum.StrEnum):
    """Lifecycle status of a proposed helper match."""

    PROPOSED = "proposed"
    """Match has been computed and is visible to the student."""

    ACCEPTED = "accepted"
    """Student acknowledged this match and expressed intent to act."""

    DISMISSED = "dismissed"
    """Student dismissed this match without further action."""

    EXPIRED = "expired"
    """Underlying need was resolved or withdrawn; match is no longer actionable."""


class HelperMatch(TimestampMixin, Base):
    __tablename__ = "helper_matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)

    # The need this match addresses.
    need_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("student_needs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The offer matched to this need.
    help_offer_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("help_offers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Institution scoping for multi-tenant queries.
    institution_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Computed relevance score in [0, 1].  Not a guarantee of suitability.
    score: Mapped[float] = mapped_column(nullable=False)

    # Ordered list of rule results that produced the score (see module docstring).
    rule_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Plain-language summary automatically derived from rule_results.
    # Must not be edited by the system after creation.
    summary_explanation: Mapped[str | None] = mapped_column(Text)

    # Uncertainty or limitations acknowledged by the engine for this match.
    uncertainty_notes: Mapped[str | None] = mapped_column(Text)

    # Version identifier of the matching rule set used to compute this match.
    scorer_version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Whether the student has seen this match.
    is_seen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Lifecycle status.
    status: Mapped[MatchStatus] = mapped_column(
        Enum(
            MatchStatus,
            native_enum=False,
            length=24,
            create_constraint=True,
            name="match_status",
            values_callable=lambda members: [m.value for m in members],
        ),
        nullable=False,
        default=MatchStatus.PROPOSED,
        index=True,
    )

    # Relationships
    need: Mapped[Any] = relationship(
        "StudentNeed",
        back_populates="matches",
        foreign_keys=[need_id],
    )
    help_offer: Mapped[Any] = relationship(
        "HelpOffer",
        back_populates="matches",
        foreign_keys=[help_offer_id],
    )
    institution: Mapped[Any] = relationship(
        "Institution",
        back_populates="helper_matches",
        foreign_keys=[institution_id],
    )
    follow_up_tasks: Mapped[list[Any]] = relationship(
        "FollowUpTask",
        back_populates="match",
        foreign_keys="[FollowUpTask.match_id]",
    )

    __table_args__ = (
        Index("ix_helper_matches_inst_status", "institution_id", "status"),
        Index("ix_helper_matches_need_score", "need_id", "score"),
    )
