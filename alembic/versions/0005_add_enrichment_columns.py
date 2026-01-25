"""Add organization enrichment columns

Revision ID: 0005_add_enrichment_columns
Revises: 0004_fix_enum_types
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005_add_enrichment_columns'
down_revision = '0004_fix_enum_types'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enrichment columns to organizations table."""
    # Add website_url column
    op.add_column('organizations', sa.Column('website_url', sa.String(512), nullable=True))
    
    # Add org_profile column (JSON stored as text)
    op.add_column('organizations', sa.Column('org_profile', sa.Text(), nullable=True))
    
    # Add baseline_suggestion column
    op.add_column('organizations', sa.Column('baseline_suggestion', sa.String(50), nullable=True))
    
    # Add enriched_at timestamp column
    op.add_column('organizations', sa.Column('enriched_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove enrichment columns from organizations table."""
    op.drop_column('organizations', 'enriched_at')
    op.drop_column('organizations', 'baseline_suggestion')
    op.drop_column('organizations', 'org_profile')
    op.drop_column('organizations', 'website_url')
