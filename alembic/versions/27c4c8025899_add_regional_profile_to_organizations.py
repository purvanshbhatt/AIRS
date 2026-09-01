"""Add regional profile to organizations

Revision ID: 27c4c8025899
Revises: 958da2dc2793
Create Date: 2026-08-11 15:28:41.305116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27c4c8025899'
down_revision: Union[str, Sequence[str], None] = '958da2dc2793'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('organizations', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('organizations', sa.Column('region_state', sa.String(length=100), nullable=True))
    op.add_column('organizations', sa.Column('regulatory_profile', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.drop_column('regulatory_profile')
        batch_op.drop_column('region_state')
        batch_op.drop_column('country')
