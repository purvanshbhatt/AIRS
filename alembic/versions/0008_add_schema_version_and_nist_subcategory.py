"""add_schema_version_to_assessments_and_nist_subcategory_to_findings

Revision ID: 0008_add_schema_version_and_nist_sub
Revises: 0007_add_nist_to_findings
Create Date: 2026-02-21

Phase 1: Adds `schema_version` (Integer, default 1) to assessments so v2
         maturity-tier questions can be differentiated from legacy v1 answers.
Phase 2: Adds `nist_subcategory` (String 50) to findings for deep NIST CSF 2.0
         notation, e.g. "DE.CM-1.1" (optional, for future granular mapping).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_add_schema_version_and_nist_sub"
down_revision: str = "0007_add_nist_to_findings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- assessments table: schema_version discriminates v1 vs v2 question sets --
    op.add_column(
        "assessments",
        sa.Column(
            "schema_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.create_index("ix_assessments_schema_version", "assessments", ["schema_version"])

    # -- findings table: nist_subcategory for deep NIST CSF 2.0 notation --
    op.add_column(
        "findings",
        sa.Column("nist_subcategory", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("findings", "nist_subcategory")
    op.drop_index("ix_assessments_schema_version", table_name="assessments")
    op.drop_column("assessments", "schema_version")
