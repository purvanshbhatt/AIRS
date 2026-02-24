"""add_external_findings_and_org_integration_status

Revision ID: 0005_add_external_findings
Revises: 0004_add_integrations
Create Date: 2026-02-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_add_external_findings"
down_revision: str = "0004_add_integrations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(
            sa.Column("integration_status", sa.Text(), nullable=False, server_default="{}")
        )

    op.create_table(
        "external_findings",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("org_id", sa.CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_external_findings_org_id", "external_findings", ["org_id"])
    op.create_index("ix_external_findings_source", "external_findings", ["source"])
    op.create_index("ix_external_findings_severity", "external_findings", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_external_findings_severity", table_name="external_findings")
    op.drop_index("ix_external_findings_source", table_name="external_findings")
    op.drop_index("ix_external_findings_org_id", table_name="external_findings")
    op.drop_table("external_findings")

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_column("integration_status")

