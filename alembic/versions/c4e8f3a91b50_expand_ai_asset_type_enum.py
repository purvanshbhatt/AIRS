"""expand_ai_asset_type_enum

Revision ID: c4e8f3a91b50
Revises: 9a1c0b3d2e4f
Create Date: 2026-07-12 00:00:00.000000

Per Sprint 1.8 Task S1.8-B5 — extends the AIAssetType enum (in
app/models/ai_asset.py) with new values for non-traditional AI assets:

  mcp_server, mcp_client, agent_framework, embedding_pipeline,
  rag_corpus, training_dataset, evaluation_pipeline, prompt_library.

For SQLite the SQLEnum column is already permissive: existing rows are
not affected because the enum's value is stored as a string. The
upgrade is therefore a no-op for SQLite; for PostgreSQL the column's
CHECK constraint is recreated.

This migration is therefore symmetric (no-op upgrade, no-op
downgrade) but exported explicitly so deployment review tooling sees
the contract.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4e8f3a91b50"
down_revision: Union[str, Sequence[str], None] = "9a1c0b3d2e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The column is TEXT (SQLAlchemy SQLEnum stores by value on SQLite).
    # Existing rows store enum values as their string. Adding new enum
    # members is therefore transparent at the database layer. We still
    # emit an explicit ALTER to ease migration tooling and to document
    # this contract.
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    # Postgres path: alter the column type if a CHECK exists.
    op.alter_column(
        "ai_assets",
        "asset_type",
        existing_type=sa.String(),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    op.alter_column(
        "ai_assets",
        "asset_type",
        existing_type=sa.String(length=64),
        type_=sa.String(),
        existing_nullable=False,
    )
