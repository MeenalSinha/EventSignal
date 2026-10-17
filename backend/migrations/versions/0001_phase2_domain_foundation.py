"""Phase 2 domain-model foundation.

Revision: 0001
Previous: None (initial migration)

Changes:
- Creates opportunities table (replaces events in Phase 1 create_all).
- Creates source_references table with opportunity_id FK (was event_id).
- Creates field_evidence table.
- Creates student_profiles table.
- Creates alumni_profiles table.
- Creates match_explanations table.
- Creates connection_requests table.

Data preservation: no existing data; the Phase 1 ``create_all`` path never
ran on a persistent database (no data/eventsignal.db existed at the start
of Phase 2). If a persistent database with events/source_references rows
does exist, this migration would fail because it cannot rename the events
table safely in SQLite without a batch migration. In that case, a separate
data migration script would be needed. The current implementation creates
the new schema for fresh installations only.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_phase2_domain_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # opportunities (replaces 'events')
    # ------------------------------------------------------------------
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(300), nullable=True),
        sa.Column(
            "opportunity_type",
            sa.Enum(
                "hackathon",
                "workshop",
                "conference",
                "competition",
                "internship",
                "fellowship",
                "research",
                "mentorship",
                "other",
                name="opportunity_type",
                native_enum=False,
                length=32,
            ),
            nullable=True,
        ),
        sa.Column("organizer", sa.String(300), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registration_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column(
            "mode",
            sa.Enum(
                "online",
                "offline",
                "hybrid",
                name="participation_mode",
                native_enum=False,
                length=16,
            ),
            nullable=True,
        ),
        sa.Column("eligibility", sa.Text, nullable=True),
        sa.Column("skills_required", sa.Text, nullable=True),
        sa.Column("compensation", sa.Text, nullable=True),
        sa.Column("application_url", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "opportunity_type IN ('hackathon','workshop','conference','competition',"
            "'internship','fellowship','research','mentorship','other')",
            name="ck_opportunities_opportunity_type",
        ),
        sa.CheckConstraint(
            "mode IN ('online','offline','hybrid')",
            name="ck_opportunities_participation_mode",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_opportunities"),
    )

    # ------------------------------------------------------------------
    # source_references
    # ------------------------------------------------------------------
    op.create_table(
        "source_references",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum(
                "opportunity_listing",
                "organizer_website",
                "registration_page",
                "announcement",
                "document",
                "social_media",
                "manual_text",
                "other",
                name="source_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("source_metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            ondelete="CASCADE",
            name="fk_source_references_opportunity_id_opportunities",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_source_references"),
        sa.UniqueConstraint("opportunity_id", "url", name="uq_source_references_opportunity_id"),
    )
    op.create_index("ix_source_references_opportunity_id", "source_references", ["opportunity_id"])

    # ------------------------------------------------------------------
    # field_evidence
    # ------------------------------------------------------------------
    op.create_table(
        "field_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("opportunity_id", sa.String(36), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("extracted_value", sa.Text, nullable=True),
        sa.Column("supporting_excerpt", sa.Text, nullable=True),
        sa.Column(
            "extraction_method",
            sa.Enum(
                "manual",
                "rule_based",
                "llm",
                "structured",
                name="extraction_method",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "evidence_status",
            sa.Enum(
                "found",
                "multi_source",
                "needs_verification",
                "not_found",
                "sources_disagree",
                "extraction_failed",
                "not_assessed",
                name="evidence_status",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["opportunities.id"],
            ondelete="CASCADE",
            name="fk_field_evidence_opportunity_id_opportunities",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["source_references.id"],
            ondelete="SET NULL",
            name="fk_field_evidence_source_id_source_references",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_field_evidence"),
    )
    op.create_index("ix_field_evidence_opportunity_id", "field_evidence", ["opportunity_id"])
    op.create_index("ix_field_evidence_source_id", "field_evidence", ["source_id"])

    # ------------------------------------------------------------------
    # student_profiles
    # ------------------------------------------------------------------
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("skills", sa.Text, nullable=True),
        sa.Column("interests", sa.Text, nullable=True),
        sa.Column("career_goals", sa.Text, nullable=True),
        sa.Column("preferred_opportunity_types", sa.Text, nullable=True),
        sa.Column("location_preference", sa.Text, nullable=True),
        sa.Column(
            "visibility",
            sa.Enum(
                "private",
                "alumni_only",
                "public",
                name="profile_visibility",
                native_enum=False,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_student_profiles"),
    )

    # ------------------------------------------------------------------
    # alumni_profiles
    # ------------------------------------------------------------------
    op.create_table(
        "alumni_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("professional_domain", sa.String(200), nullable=True),
        sa.Column("skills", sa.Text, nullable=True),
        sa.Column("industry", sa.Text, nullable=True),
        sa.Column("years_experience", sa.Integer, nullable=True),
        sa.Column("mentoring_interests", sa.Text, nullable=True),
        sa.Column("willing_to_connect", sa.Boolean, nullable=False),
        sa.Column("monthly_connection_limit", sa.Integer, nullable=True),
        sa.Column(
            "visibility",
            sa.Enum(
                "private",
                "students_only",
                "public",
                name="alumni_profile_visibility",
                native_enum=False,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_alumni_profiles"),
    )

    # ------------------------------------------------------------------
    # match_explanations
    # ------------------------------------------------------------------
    op.create_table(
        "match_explanations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("student_profile_id", sa.String(36), nullable=False),
        sa.Column(
            "matched_entity_type",
            sa.Enum(
                "opportunity",
                "alumni",
                name="matched_entity_type",
                native_enum=False,
                length=24,
            ),
            nullable=False,
        ),
        sa.Column("matched_entity_id", sa.String(36), nullable=False),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("reasons", sa.JSON, nullable=False),
        sa.Column("contributing_attributes", sa.JSON, nullable=True),
        sa.Column("uncertainty_notes", sa.Text, nullable=True),
        sa.Column("scorer_version", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["student_profile_id"],
            ["student_profiles.id"],
            ondelete="CASCADE",
            name="fk_match_explanations_student_profile_id_student_profiles",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_match_explanations"),
    )
    op.create_index(
        "ix_match_explanations_student_profile_id",
        "match_explanations",
        ["student_profile_id"],
    )
    op.create_index(
        "ix_match_explanations_matched_entity_id",
        "match_explanations",
        ["matched_entity_id"],
    )

    # ------------------------------------------------------------------
    # connection_requests
    # ------------------------------------------------------------------
    op.create_table(
        "connection_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("requester_profile_id", sa.String(36), nullable=False),
        sa.Column("recipient_profile_id", sa.String(36), nullable=False),
        sa.Column(
            "purpose",
            sa.Enum(
                "career_guidance",
                "opportunity_specific",
                "skill_mentoring",
                "industry_insight",
                "referral",
                "other",
                name="connection_purpose",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "accepted",
                "declined",
                "withdrawn",
                "expired",
                name="request_status",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["requester_profile_id"],
            ["student_profiles.id"],
            ondelete="CASCADE",
            name="fk_connection_requests_requester_profile_id_student_profiles",
        ),
        sa.ForeignKeyConstraint(
            ["recipient_profile_id"],
            ["alumni_profiles.id"],
            ondelete="CASCADE",
            name="fk_connection_requests_recipient_profile_id_alumni_profiles",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_connection_requests"),
    )
    op.create_index(
        "ix_connection_requests_requester_profile_id",
        "connection_requests",
        ["requester_profile_id"],
    )
    op.create_index(
        "ix_connection_requests_recipient_profile_id",
        "connection_requests",
        ["recipient_profile_id"],
    )


def downgrade() -> None:
    op.drop_table("connection_requests")
    op.drop_table("match_explanations")
    op.drop_table("alumni_profiles")
    op.drop_table("student_profiles")
    op.drop_table("field_evidence")
    op.drop_table("source_references")
    op.drop_table("opportunities")
