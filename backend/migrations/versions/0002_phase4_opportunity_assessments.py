"""Phase 4: opportunity_assessments table.

Revision: 0002_phase4_opportunity_assessments
Previous: 0001_phase2_domain_foundation

Changes:
- Creates opportunity_assessments table to persist evaluation results
  produced by the Phase 4 assessment engine.

Each assessment record captures five evaluation dimensions:
  completeness, evidence_quality, cross_source_consistency,
  missing_critical, ambiguous_or_conflicting.

Plus free-text explanation fields and an overall score (0.0–1.0).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_phase4_opportunity_assessments"
down_revision: str | None = "0001_phase2_domain_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "opportunity_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.String(36),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Overall composite score (0.0 = nothing known; 1.0 = fully evidenced)
        sa.Column("overall_score", sa.Float(), nullable=False),
        # Dimension scores (0.0–1.0 each)
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("evidence_quality_score", sa.Float(), nullable=False),
        sa.Column("consistency_score", sa.Float(), nullable=False),
        # Explanation text for each dimension
        sa.Column("completeness_explanation", sa.Text(), nullable=False),
        sa.Column("evidence_quality_explanation", sa.Text(), nullable=False),
        sa.Column("consistency_explanation", sa.Text(), nullable=False),
        # Structured field lists (stored as JSON)
        sa.Column("missing_critical_fields", sa.JSON(), nullable=False, default="[]"),
        sa.Column("missing_optional_fields", sa.JSON(), nullable=False, default="[]"),
        sa.Column("ambiguous_fields", sa.JSON(), nullable=False, default="[]"),
        sa.Column("conflicting_fields", sa.JSON(), nullable=False, default="[]"),
        # Limitations / caveats paragraph
        sa.Column("limitations", sa.Text(), nullable=False),
        # Snapshot of evidence field count at assessment time
        sa.Column("total_fields_assessed", sa.Integer(), nullable=False),
        sa.Column("fields_found_count", sa.Integer(), nullable=False),
        sa.Column("fields_not_found_count", sa.Integer(), nullable=False),
        sa.Column("fields_failed_count", sa.Integer(), nullable=False),
        # Timestamps
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


def downgrade() -> None:
    op.drop_table("opportunity_assessments")
