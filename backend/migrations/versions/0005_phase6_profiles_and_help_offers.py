"""Phase 6: campus network, user-owned profiles, and explicit help offers.

Revision: 0005_phase6_profiles_and_help_offers
Previous: 0004_phase5_institutional_identity_and_access

Changes:
- Adds user_id, institution_id, membership_id and unique constraint to student_profiles.
- Adds user_id, institution_id, membership_id and unique constraint to alumni_profiles.
- Creates help_offers table for explicit declared assistance offers with lifecycle & consent.
- Adds optional help_offer_id to connection_requests table.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_phase6_profiles_and_help_offers"
down_revision: str | None = "0004_phase5_institutional_identity_and_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update student_profiles with user and institution ownership
    with op.batch_alter_table("student_profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "institution_id",
                sa.String(36),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "membership_id",
                sa.String(36),
                sa.ForeignKey("institution_memberships.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.create_index("ix_student_profiles_user_id", ["user_id"])
        batch_op.create_index("ix_student_profiles_institution_id", ["institution_id"])
        batch_op.create_index("ix_student_profiles_membership_id", ["membership_id"])
        batch_op.create_unique_constraint(
            "uq_student_profile_user_institution",
            ["user_id", "institution_id"],
        )

    # 2. Update alumni_profiles with user and institution ownership
    with op.batch_alter_table("alumni_profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "user_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "institution_id",
                sa.String(36),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "membership_id",
                sa.String(36),
                sa.ForeignKey("institution_memberships.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.create_index("ix_alumni_profiles_user_id", ["user_id"])
        batch_op.create_index("ix_alumni_profiles_institution_id", ["institution_id"])
        batch_op.create_index("ix_alumni_profiles_membership_id", ["membership_id"])
        batch_op.create_unique_constraint(
            "uq_alumni_profile_user_institution",
            ["user_id", "institution_id"],
        )

    # 3. Create help_offers table
    op.create_table(
        "help_offers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "membership_id",
            sa.String(36),
            sa.ForeignKey("institution_memberships.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("applicable_skills", sa.Text(), nullable=True),
        sa.Column("intended_audience", sa.String(64), nullable=False, server_default="all"),
        sa.Column("delivery_mode", sa.String(64), nullable=False, server_default="remote"),
        sa.Column("availability_description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active", index=True),
        sa.Column("willing_to_help", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("extra_data", sa.JSON(), nullable=True),
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
        "ix_help_offers_inst_status",
        "help_offers",
        ["institution_id", "status"],
    )
    op.create_index(
        "ix_help_offers_inst_category",
        "help_offers",
        ["institution_id", "category"],
    )

    # 4. Add help_offer_id to connection_requests
    with op.batch_alter_table("connection_requests") as batch_op:
        batch_op.add_column(
            sa.Column(
                "help_offer_id",
                sa.String(36),
                sa.ForeignKey("help_offers.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.create_index("ix_connection_requests_help_offer_id", ["help_offer_id"])


def downgrade() -> None:
    with op.batch_alter_table("connection_requests") as batch_op:
        batch_op.drop_index("ix_connection_requests_help_offer_id")
        batch_op.drop_column("help_offer_id")

    op.drop_index("ix_help_offers_inst_category", table_name="help_offers")
    op.drop_index("ix_help_offers_inst_status", table_name="help_offers")
    op.drop_table("help_offers")

    with op.batch_alter_table("alumni_profiles") as batch_op:
        batch_op.drop_constraint("uq_alumni_profile_user_institution", type_="unique")
        batch_op.drop_index("ix_alumni_profiles_membership_id")
        batch_op.drop_index("ix_alumni_profiles_institution_id")
        batch_op.drop_index("ix_alumni_profiles_user_id")
        batch_op.drop_column("membership_id")
        batch_op.drop_column("institution_id")
        batch_op.drop_column("user_id")

    with op.batch_alter_table("student_profiles") as batch_op:
        batch_op.drop_constraint("uq_student_profile_user_institution", type_="unique")
        batch_op.drop_index("ix_student_profiles_membership_id")
        batch_op.drop_index("ix_student_profiles_institution_id")
        batch_op.drop_index("ix_student_profiles_user_id")
        batch_op.drop_column("membership_id")
        batch_op.drop_column("institution_id")
        batch_op.drop_column("user_id")
