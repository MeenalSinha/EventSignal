"""Add media_assets table for Cloudinary integration.

Revision: 0008_cloudinary_media_assets
Previous: 0007_phase8_partnerships_promotion_pilot

Changes:
- Creates media_assets table (Cloudinary-backed persistent media references).
- Enforces institutional isolation and record association (opportunities, event memories, handovers).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_cloudinary_media_assets"
down_revision: str | None = "0007_phase8_partnerships_promotion_pilot"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cloudinary_public_id", sa.String(255), nullable=False, unique=True),
        sa.Column("secure_url", sa.String(1024), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False, server_default="image"),
        sa.Column("format", sa.String(16), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("alt_text", sa.String(255), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("media_purpose", sa.String(64), nullable=False, server_default="opportunity_poster"),
        sa.Column(
            "institution_id",
            sa.String(36),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "uploader_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "opportunity_id",
            sa.String(36),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "event_memory_id",
            sa.String(36),
            sa.ForeignKey("event_memories.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "legacy_handover_id",
            sa.String(36),
            sa.ForeignKey("legacy_handovers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_media_assets_cloudinary_public_id", "media_assets", ["cloudinary_public_id"])
    op.create_index("ix_media_assets_institution_id", "media_assets", ["institution_id"])
    op.create_index("ix_media_assets_uploader_user_id", "media_assets", ["uploader_user_id"])
    op.create_index("ix_media_assets_opportunity_id", "media_assets", ["opportunity_id"])
    op.create_index("ix_media_assets_event_memory_id", "media_assets", ["event_memory_id"])
    op.create_index("ix_media_assets_legacy_handover_id", "media_assets", ["legacy_handover_id"])
    op.create_index("ix_media_assets_media_purpose", "media_assets", ["media_purpose"])


def downgrade() -> None:
    op.drop_index("ix_media_assets_media_purpose", table_name="media_assets")
    op.drop_index("ix_media_assets_legacy_handover_id", table_name="media_assets")
    op.drop_index("ix_media_assets_event_memory_id", table_name="media_assets")
    op.drop_index("ix_media_assets_opportunity_id", table_name="media_assets")
    op.drop_index("ix_media_assets_uploader_user_id", table_name="media_assets")
    op.drop_index("ix_media_assets_institution_id", table_name="media_assets")
    op.drop_index("ix_media_assets_cloudinary_public_id", table_name="media_assets")
    op.drop_table("media_assets")
