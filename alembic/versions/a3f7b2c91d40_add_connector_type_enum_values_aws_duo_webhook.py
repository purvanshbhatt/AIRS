"""add_connector_type_enum_values_aws_duo_webhook

Revision ID: a3f7b2c91d40
Revises: 27c4c8025899
Create Date: 2026-09-20 22:42:00.000000

Adds 'aws', 'duo', and 'webhook' to the ConnectorType enum so the
frontend connector configuration forms can save all supported types.

For SQLite the column stores enum values as TEXT strings, so new members
are transparent. For PostgreSQL the native enum type must be altered.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f7b2c91d40"
down_revision: Union[str, Sequence[str], None] = "27c4c8025899"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_VALUES = ["aws", "duo", "webhook"]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite stores enum values as plain TEXT - no schema change needed.
        return

    # PostgreSQL: add new values to the native enum type.
    for val in NEW_VALUES:
        op.execute(
            sa.text(
                f"ALTER TYPE connectortype ADD VALUE IF NOT EXISTS '{val}'"
            )
        )


def downgrade() -> None:
    # PostgreSQL enums do not support removing values.
    # The values are harmless if unused, so downgrade is a no-op.
    pass
