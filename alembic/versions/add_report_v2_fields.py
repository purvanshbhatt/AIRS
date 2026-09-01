"""Add V2 report lifecycle fields.

Revision ID: a3c8e5f91b42
Revises: 27c4c8025899
Create Date: 2026-09-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a3c8e5f91b42'
down_revision = None  # standalone migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add V2 report lifecycle columns
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.String(128), nullable=True))
        batch_op.add_column(sa.Column('report_version', sa.String(20), nullable=False, server_default='1.0'))
        batch_op.add_column(sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(20), nullable=False, server_default='completed'))


def downgrade() -> None:
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('generated_at')
        batch_op.drop_column('report_version')
        batch_op.drop_column('created_by')
