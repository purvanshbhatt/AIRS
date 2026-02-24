"""add_question_metadata_table

Revision ID: 0007_add_question_metadata
Revises: 0006_add_audit_and_pilot
Create Date: 2026-02-23

Adds the ``question_metadata`` table for per-question enrichment data
(framework_tags, maturity_level, effort_level, impact_level, control_function).

Backward compatible: new table only, no existing table modifications.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = "0007_add_question_metadata"
down_revision: str = "0006_add_audit_and_pilot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_metadata",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("question_id", sa.String(length=20), nullable=False),
        sa.Column("framework_tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "maturity_level",
            sa.Enum("basic", "managed", "advanced", name="maturitylevel"),
            nullable=False,
            server_default="basic",
        ),
        sa.Column(
            "effort_level",
            sa.Enum("low", "medium", "high", name="effortlevel"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "impact_level",
            sa.Enum("low", "medium", "high", name="impactlevel"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "control_function",
            sa.Enum("govern", "identify", "protect", "detect", "respond", "recover", name="controlfunction"),
            nullable=False,
            server_default="detect",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_question_metadata_question_id", "question_metadata", ["question_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_question_metadata_question_id", table_name="question_metadata")
    op.drop_table("question_metadata")
