"""Add tactic and technique to TelemetryEvidence

Revision ID: 7ee3bdafe488
Revises: b88ca5746ac1
Create Date: 2026-06-15 11:35:47.522725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7ee3bdafe488"
down_revision: Union[str, Sequence[str], None] = "b88ca5746ac1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("telemetry_evidence", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tactic", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("technique", sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("telemetry_evidence", schema=None) as batch_op:
        batch_op.drop_column("technique")
        batch_op.drop_column("tactic")

