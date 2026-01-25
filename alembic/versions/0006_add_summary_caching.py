"""Add summary and narrative caching columns to assessments.

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-25

This migration adds columns for caching computed summary payloads and LLM narratives
to reduce latency on GET /api/assessments/{id}/summary.

Fields added:
- summary_json: Cached JSON payload of the full summary
- summary_version: Increments when answers/scoring change (triggers recompute)
- summary_computed_at: Timestamp of when summary was last computed
- narrative_executive: Cached LLM executive summary text
- narrative_roadmap: Cached LLM roadmap narrative text
- narrative_version: Version when narratives were generated
- narrative_generated_at: Timestamp of when narratives were last generated
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add caching columns to assessments table."""
    # Summary caching columns
    op.add_column('assessments', sa.Column('summary_json', sa.Text(), nullable=True))
    op.add_column('assessments', sa.Column('summary_version', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('assessments', sa.Column('summary_computed_at', sa.DateTime(timezone=True), nullable=True))
    
    # Narrative caching columns
    op.add_column('assessments', sa.Column('narrative_executive', sa.Text(), nullable=True))
    op.add_column('assessments', sa.Column('narrative_roadmap', sa.Text(), nullable=True))
    op.add_column('assessments', sa.Column('narrative_version', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('assessments', sa.Column('narrative_generated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove caching columns from assessments table."""
    op.drop_column('assessments', 'narrative_generated_at')
    op.drop_column('assessments', 'narrative_version')
    op.drop_column('assessments', 'narrative_roadmap')
    op.drop_column('assessments', 'narrative_executive')
    op.drop_column('assessments', 'summary_computed_at')
    op.drop_column('assessments', 'summary_version')
    op.drop_column('assessments', 'summary_json')
