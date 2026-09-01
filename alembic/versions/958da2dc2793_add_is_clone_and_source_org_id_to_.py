"""Add is_clone and source_org_id to Organization

Revision ID: 958da2dc2793
Revises: c4e8f3a91b50
Create Date: 2026-07-12 21:11:22.131960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '958da2dc2793'
down_revision: Union[str, Sequence[str], None] = 'c4e8f3a91b50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('organizations') as batch_op:
        batch_op.add_column(sa.Column('is_clone', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('source_org_id', sa.CHAR(length=36), nullable=True))
        batch_op.create_foreign_key('fk_organizations_source_org_id', 'organizations', ['source_org_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('organizations') as batch_op:
        batch_op.drop_constraint('fk_organizations_source_org_id', type_='foreignkey')
        batch_op.drop_column('source_org_id')
        batch_op.drop_column('is_clone')
