"""Phase 8: Partnerships, Cross-College Promotion, Pilot & Release.

Revision: 0007_phase8_partnerships_promotion_pilot
Previous: 0006_phase7_matching_and_legacy

Changes:
- Creates partner_organizations table (external brands, partners, and verification status).
- Creates sponsorship_requests table (structured event sponsorship prospectuses).
- Creates promotion_campaigns table (cross-college promotion requests with disclosure).
- Creates alumni_import_jobs table (institutional batch import logs and audit trail).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_phase8_partnerships_promotion_pilot"
down_revision: str | None = "0006_phase7_matching_and_legacy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. partner_organizations
    op.create_table(
        "partner_organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column(
            "verification_status", sa.String(32), nullable=False, server_default="unverified"
        ),
        sa.Column("notes", sa.Text, nullable=True),
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
    op.create_index(
        "ix_partner_org_inst_name",
        "partner_organizations",
        ["institution_id", "name"],
    )

    # 2. sponsorship_requests
    op.create_table(
        "sponsorship_requests",
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
            nullable=True,
        ),
        sa.Column(
            "organizer_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "partner_organization_id",
            sa.String(36),
            sa.ForeignKey("partner_organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("objective", sa.String(255), nullable=False),
        sa.Column("support_type", sa.String(32), nullable=False, server_default="financial"),
        sa.Column("proposed_benefits", sa.Text, nullable=False),
        sa.Column("intended_audience", sa.String(255), nullable=True),
        sa.Column("budget_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("budget_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("commercial_terms", sa.JSON, nullable=True),
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
    op.create_index(
        "ix_sponsorship_inst_status",
        "sponsorship_requests",
        ["institution_id", "status"],
    )

    # 3. promotion_campaigns
    op.create_table(
        "promotion_campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "source_institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "opportunity_id",
            sa.String(36),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "creator_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_institution_ids", sa.JSON, nullable=False),
        sa.Column(
            "campaign_type", sa.String(32), nullable=False, server_default="featured_spotlight"
        ),
        sa.Column(
            "pricing_package",
            sa.String(100),
            nullable=False,
            server_default="standard_cross_college",
        ),
        sa.Column("price_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column(
            "reviewer_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("is_paid_placement", sa.Boolean, nullable=False, server_default=sa.true()),
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
    op.create_index(
        "ix_campaign_source_status",
        "promotion_campaigns",
        ["source_institution_id", "status"],
    )

    # 4. alumni_import_jobs
    op.create_table(
        "alumni_import_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploader_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="preview"),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("accepted_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("skipped_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rejected_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("validation_errors", sa.JSON, nullable=False),
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
    op.create_index(
        "ix_alumni_import_inst_status",
        "alumni_import_jobs",
        ["institution_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("alumni_import_jobs")
    op.drop_table("promotion_campaigns")
    op.drop_table("sponsorship_requests")
    op.drop_table("partner_organizations")
