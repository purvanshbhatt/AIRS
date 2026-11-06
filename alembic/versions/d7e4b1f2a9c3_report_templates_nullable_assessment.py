"""Report templates: nullable assessment_id and format column.

Revision ID: d7e4b1f2a9c3
Revises: 01c8a208e094, a3f7b2c91d40
Create Date: 2026-11-06

Template reports (board_story, boss_report, msp_summary, cyber_insurance, ...)
are built from readiness telemetry rather than a questionnaire assessment, so
``reports.assessment_id`` becomes nullable. A ``format`` column records the
output format requested at generation time (pdf | json | csv).

This revision also merges the two outstanding heads.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d7e4b1f2a9c3"
down_revision: Union[str, Sequence[str], None] = ("01c8a208e094", "a3f7b2c91d40")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("reports", schema=None) as batch_op:
        batch_op.alter_column(
            "assessment_id",
            existing_type=sa.CHAR(36),
            nullable=True,
        )
        batch_op.add_column(
            sa.Column("format", sa.String(10), nullable=False, server_default="pdf")
        )


def downgrade() -> None:
    with op.batch_alter_table("reports", schema=None) as batch_op:
        batch_op.drop_column("format")
        batch_op.alter_column(
            "assessment_id",
            existing_type=sa.CHAR(36),
            nullable=False,
        )
