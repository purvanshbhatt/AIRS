"""add_nist_columns_to_findings

Revision ID: 0007_add_nist_to_findings
Revises: 0006_add_audit_and_pilot
Create Date: 2026-02-21

Adds nist_function and nist_category columns to the findings table to support
NIST CSF 2.0 lifecycle mapping (Govern/Identify/Protect/Detect/Respond/Recover)
and granular category notation (e.g. DE.CM-1, PR.AA-5, RS.MA-1).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0007_add_nist_to_findings"
down_revision: str = "0006_add_audit_and_pilot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nist_function: short lifecycle function code, e.g. "GV", "ID", "PR", "DE", "RS", "RC"
    op.add_column(
        "findings",
        sa.Column("nist_function", sa.String(length=10), nullable=True),
    )

    # Add nist_category: dotted notation category, e.g. "DE.CM-1", "PR.AA-5", "RS.MA-1"
    op.add_column(
        "findings",
        sa.Column("nist_category", sa.String(length=20), nullable=True),
    )

    # Index on nist_function to allow filtering by lifecycle stage
    op.create_index(
        "ix_findings_nist_function",
        "findings",
        ["nist_function"],
    )


def downgrade() -> None:
    op.drop_index("ix_findings_nist_function", table_name="findings")
    op.drop_column("findings", "nist_category")
    op.drop_column("findings", "nist_function")
