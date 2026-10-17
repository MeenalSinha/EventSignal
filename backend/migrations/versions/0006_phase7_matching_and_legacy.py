"""Phase 7: Gap-to-Helper Matching & EventSignal Legacy.

Revision: 0006_phase7_matching_and_legacy
Previous: 0005_phase6_profiles_and_help_offers

Changes:
- Creates student_needs table (declared student gaps / blockers).
- Creates helper_matches table (rule-evaluated need-to-offer matches).
- Creates legacy_handovers table (structured knowledge-transfer documents).
- Creates event_memories table (institutional memory for events/opportunities).
- Creates follow_up_tasks table (actionable tasks from handovers and matches).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_phase7_matching_and_legacy"
down_revision: str | None = "0005_phase6_profiles_and_help_offers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. student_needs
    op.create_table(
        "student_needs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "student_profile_id",
            sa.String(36),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("preferred_delivery_mode", sa.String(64)),
        sa.Column("urgency", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(24), nullable=False, server_default="open"),
        sa.Column("extra_data", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_student_needs_student_profile_id", "student_needs", ["student_profile_id"])
    op.create_index("ix_student_needs_institution_id", "student_needs", ["institution_id"])
    op.create_index("ix_student_needs_status", "student_needs", ["status"])
    op.create_index("ix_student_needs_category", "student_needs", ["category"])
    op.create_index(
        "ix_student_needs_inst_status", "student_needs", ["institution_id", "status"]
    )
    op.create_index(
        "ix_student_needs_inst_category", "student_needs", ["institution_id", "category"]
    )

    # 2. helper_matches
    op.create_table(
        "helper_matches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "need_id",
            sa.String(36),
            sa.ForeignKey("student_needs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "help_offer_id",
            sa.String(36),
            sa.ForeignKey("help_offers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("rule_results", sa.JSON, nullable=False),
        sa.Column("summary_explanation", sa.Text),
        sa.Column("uncertainty_notes", sa.Text),
        sa.Column("scorer_version", sa.String(50), nullable=False),
        sa.Column("is_seen", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="proposed"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_helper_matches_need_id", "helper_matches", ["need_id"])
    op.create_index("ix_helper_matches_help_offer_id", "helper_matches", ["help_offer_id"])
    op.create_index("ix_helper_matches_institution_id", "helper_matches", ["institution_id"])
    op.create_index("ix_helper_matches_status", "helper_matches", ["status"])
    op.create_index(
        "ix_helper_matches_inst_status", "helper_matches", ["institution_id", "status"]
    )
    op.create_index("ix_helper_matches_need_score", "helper_matches", ["need_id", "score"])

    # 3. legacy_handovers
    op.create_table(
        "legacy_handovers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "position_id",
            sa.String(36),
            sa.ForeignKey("campus_position_definitions.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "outgoing_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "incoming_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("accomplishments_summary", sa.Text),
        sa.Column("ongoing_work", sa.Text),
        sa.Column("key_contacts", sa.JSON, nullable=False),
        sa.Column("lessons_learned", sa.Text),
        sa.Column("recommended_first_steps", sa.Text),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_legacy_handovers_institution_id", "legacy_handovers", ["institution_id"])
    op.create_index("ix_legacy_handovers_position_id", "legacy_handovers", ["position_id"])
    op.create_index(
        "ix_legacy_handovers_outgoing_user_id", "legacy_handovers", ["outgoing_user_id"]
    )
    op.create_index(
        "ix_legacy_handovers_incoming_user_id", "legacy_handovers", ["incoming_user_id"]
    )
    op.create_index("ix_legacy_handovers_status", "legacy_handovers", ["status"])
    op.create_index(
        "ix_legacy_handovers_inst_status", "legacy_handovers", ["institution_id", "status"]
    )
    op.create_index(
        "ix_legacy_handovers_position", "legacy_handovers", ["position_id", "version"]
    )

    # 4. event_memories
    op.create_table(
        "event_memories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "opportunity_id",
            sa.String(36),
            sa.ForeignKey("opportunities.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "handover_id",
            sa.String(36),
            sa.ForeignKey("legacy_handovers.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "author_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("what_worked", sa.Text),
        sa.Column("what_did_not_work", sa.Text),
        sa.Column("attendance_notes", sa.Text),
        sa.Column("outcome_summary", sa.Text),
        sa.Column("context_notes", sa.Text),
        sa.Column("tags", sa.JSON, nullable=False),
        sa.Column("superseded_by_id", sa.String(36)),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("extra_data", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_event_memories_institution_id", "event_memories", ["institution_id"])
    op.create_index("ix_event_memories_opportunity_id", "event_memories", ["opportunity_id"])
    op.create_index("ix_event_memories_handover_id", "event_memories", ["handover_id"])
    op.create_index("ix_event_memories_author_user_id", "event_memories", ["author_user_id"])
    op.create_index("ix_event_memories_is_current", "event_memories", ["is_current"])
    op.create_index("ix_event_memories_superseded_by_id", "event_memories", ["superseded_by_id"])
    op.create_index(
        "ix_event_memories_inst_current", "event_memories", ["institution_id", "is_current"]
    )
    op.create_index(
        "ix_event_memories_opportunity", "event_memories", ["opportunity_id", "is_current"]
    )

    # 5. follow_up_tasks
    op.create_table(
        "follow_up_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(24), nullable=False, server_default="manual"),
        sa.Column(
            "handover_id",
            sa.String(36),
            sa.ForeignKey("legacy_handovers.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "match_id",
            sa.String(36),
            sa.ForeignKey("helper_matches.id", ondelete="SET NULL"),
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "assignee_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "creator_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("priority", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("is_completed", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("extra_data", sa.JSON),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_follow_up_tasks_institution_id", "follow_up_tasks", ["institution_id"])
    op.create_index("ix_follow_up_tasks_source", "follow_up_tasks", ["source"])
    op.create_index("ix_follow_up_tasks_handover_id", "follow_up_tasks", ["handover_id"])
    op.create_index("ix_follow_up_tasks_match_id", "follow_up_tasks", ["match_id"])
    op.create_index("ix_follow_up_tasks_assignee_user_id", "follow_up_tasks", ["assignee_user_id"])
    op.create_index("ix_follow_up_tasks_creator_user_id", "follow_up_tasks", ["creator_user_id"])
    op.create_index("ix_follow_up_tasks_priority", "follow_up_tasks", ["priority"])
    op.create_index("ix_follow_up_tasks_is_completed", "follow_up_tasks", ["is_completed"])
    op.create_index(
        "ix_follow_up_tasks_inst_completed",
        "follow_up_tasks",
        ["institution_id", "is_completed"],
    )
    op.create_index(
        "ix_follow_up_tasks_assignee_completed",
        "follow_up_tasks",
        ["assignee_user_id", "is_completed"],
    )


def downgrade() -> None:
    op.drop_table("follow_up_tasks")
    op.drop_table("event_memories")
    op.drop_table("legacy_handovers")
    op.drop_table("helper_matches")
    op.drop_table("student_needs")
