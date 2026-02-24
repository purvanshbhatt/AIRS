"""add_analytics_enabled_to_organizations

Revision ID: 0009_add_analytics_flag
Revises: 0008_add_schema_version_and_nist_sub
Create Date: 2026-02-21

Phase 5 (Governance & Analytics Control):
Adds `analytics_enabled` (Boolean, default True) to the organizations table.
When False, the middleware skips telemetry emission and behavioral analytics
logging for all assessments belonging to that organization.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009_add_analytics_flag"
down_revision: str = "0008_add_schema_version_and_nist_sub"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column(
            "analytics_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("organizations", "analytics_enabled")
