"""add_readiness_ledger_entries

Revision ID: 9a1c0b3d2e4f
Revises: 7ee3bdafe488
Create Date: 2026-07-12 00:00:00.000000

Adds ReadinessLedgerEntry per ADR-008 — immutable, audit-grade ledger of score
recalculations. Idempotency index on (org_id, timestamp, new_score).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = "9a1c0b3d2e4f"
down_revision: Union[str, Sequence[str], None] = "7ee3bdafe488"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create readiness_ledger_entries (immutable)."""
    op.create_table(
        "readiness_ledger_entries",
        sa.Column("id", sqlite.CHAR(36), primary_key=True),
        sa.Column(
            "org_id",
            sqlite.CHAR(36),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("previous_score", sa.Float, nullable=False),
        sa.Column("new_score", sa.Float, nullable=False),
        sa.Column("delta", sa.Float, nullable=False),
        sa.Column("driver_type", sa.String(length=64), nullable=True),
        sa.Column("driver_item", sa.String(length=255), nullable=True),
        sa.Column("impact", sa.Float, nullable=True),
        sa.Column("evidence_source", sa.String(length=128), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_readiness_ledger_org_timestamp",
        "readiness_ledger_entries",
        ["org_id", "timestamp"],
    )
    op.create_index(
        "ix_readiness_ledger_idempotency",
        "readiness_ledger_entries",
        ["org_id", "timestamp", "new_score"],
    )


def downgrade() -> None:
    """Drop readiness_ledger_entries."""
    op.drop_index(
        "ix_readiness_ledger_idempotency",
        table_name="readiness_ledger_entries",
    )
    op.drop_index(
        "ix_readiness_ledger_org_timestamp",
        table_name="readiness_ledger_entries",
    )
    op.drop_table("readiness_ledger_entries")
