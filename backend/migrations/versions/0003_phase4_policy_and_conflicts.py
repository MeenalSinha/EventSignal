"""Phase 4: add policy_version and conflict_details to opportunity_assessments.

Revision: 0003_phase4_policy_and_conflicts
Previous: 0002_phase4_opportunity_assessments
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase4_policy_and_conflicts"
down_revision: str | None = "0002_phase4_opportunity_assessments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("opportunity_assessments") as batch_op:
        batch_op.add_column(
            sa.Column(
                "policy_version",
                sa.String(32),
                nullable=False,
                server_default="1.0.0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "conflict_details",
                sa.JSON(),
                nullable=False,
                server_default="[]",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("opportunity_assessments") as batch_op:
        batch_op.drop_column("conflict_details")
        batch_op.drop_column("policy_version")
