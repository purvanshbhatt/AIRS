"""add_reports_table

Revision ID: 0003_add_reports
Revises: 0002_add_owner_uid
Create Date: 2026-01-21

Add reports table for persistent report storage with snapshot data.
Reports capture point-in-time assessment data for consistency.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_add_reports'
down_revision: str = '0002_add_owner_uid'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reports table with indexes."""
    
    op.create_table(
        'reports',
        # Primary key
        sa.Column('id', sa.CHAR(36), primary_key=True),
        
        # Tenant isolation
        sa.Column('owner_uid', sa.String(128), nullable=False),
        
        # Foreign keys
        sa.Column('organization_id', sa.CHAR(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('assessment_id', sa.CHAR(36), sa.ForeignKey('assessments.id'), nullable=False),
        
        # Report metadata
        sa.Column('report_type', sa.String(50), nullable=False, server_default='executive_pdf'),
        sa.Column('title', sa.String(255), nullable=False),
        
        # Storage reference
        sa.Column('storage_path', sa.String(512), nullable=True),
        
        # Snapshot data (JSON)
        sa.Column('snapshot', sa.Text, nullable=False),
        
        # Cached values for efficient querying
        sa.Column('overall_score', sa.Float, nullable=True),
        sa.Column('maturity_level', sa.Integer, nullable=True),
        sa.Column('maturity_name', sa.String(50), nullable=True),
        sa.Column('findings_count', sa.Integer, nullable=True, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes for efficient queries
    op.create_index('ix_reports_owner_uid', 'reports', ['owner_uid'])
    op.create_index('ix_reports_organization_id', 'reports', ['organization_id'])
    op.create_index('ix_reports_assessment_id', 'reports', ['assessment_id'])
    op.create_index('ix_reports_created_at', 'reports', ['created_at'])


def downgrade() -> None:
    """Drop reports table."""
    op.drop_index('ix_reports_created_at', 'reports')
    op.drop_index('ix_reports_assessment_id', 'reports')
    op.drop_index('ix_reports_organization_id', 'reports')
    op.drop_index('ix_reports_owner_uid', 'reports')
    op.drop_table('reports')
