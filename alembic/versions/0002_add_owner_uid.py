"""add_owner_uid

Revision ID: 0002_add_owner_uid
Revises: 0001_initial_schema
Create Date: 2026-01-21

Add owner_uid column to organizations and assessments tables for tenant isolation.
This ensures users can only access their own data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_add_owner_uid'
down_revision: str = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add owner_uid columns with indexes."""
    
    # Add owner_uid to organizations
    op.add_column('organizations', sa.Column('owner_uid', sa.String(128), nullable=True))
    op.create_index('ix_organizations_owner_uid', 'organizations', ['owner_uid'])
    
    # Add owner_uid to assessments
    op.add_column('assessments', sa.Column('owner_uid', sa.String(128), nullable=True))
    op.create_index('ix_assessments_owner_uid', 'assessments', ['owner_uid'])
    
    # Note: For existing data, owner_uid will be NULL.
    # In production, you may want to:
    # 1. Run a data migration to assign existing records to a specific user
    # 2. Then alter the column to be non-nullable
    # For now, we keep it nullable to avoid breaking existing data.


def downgrade() -> None:
    """Remove owner_uid columns."""
    op.drop_index('ix_assessments_owner_uid', 'assessments')
    op.drop_column('assessments', 'owner_uid')
    
    op.drop_index('ix_organizations_owner_uid', 'organizations')
    op.drop_column('organizations', 'owner_uid')
