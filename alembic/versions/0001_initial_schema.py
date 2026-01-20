"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-01-19

Initial database schema for AIRS.
Creates all tables for organizations, assessments, answers, scores, and findings.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    
    # Organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('size', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Assessments table
    op.create_table(
        'assessments',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('version', sa.String(20), server_default='1.0.0'),
        sa.Column('status', sa.String(20), server_default='draft'),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('maturity_level', sa.Integer(), nullable=True),
        sa.Column('maturity_name', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_assessments_organization_id', 'assessments', ['organization_id'])
    op.create_index('ix_assessments_status', 'assessments', ['status'])

    # Answers table
    op.create_table(
        'answers',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('assessment_id', sa.CHAR(36), sa.ForeignKey('assessments.id'), nullable=False),
        sa.Column('question_id', sa.String(20), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_answers_assessment_id', 'answers', ['assessment_id'])
    op.create_index('ix_answers_question_id', 'answers', ['question_id'])

    # Scores table
    op.create_table(
        'scores',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('assessment_id', sa.CHAR(36), sa.ForeignKey('assessments.id'), nullable=False),
        sa.Column('domain_id', sa.String(50), nullable=False),
        sa.Column('domain_name', sa.String(100), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('max_score', sa.Float(), server_default='5.0'),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('weighted_score', sa.Float(), nullable=False),
        sa.Column('raw_points', sa.Float(), nullable=True),
        sa.Column('max_raw_points', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_scores_assessment_id', 'scores', ['assessment_id'])
    op.create_index('ix_scores_domain_id', 'scores', ['domain_id'])

    # Findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('assessment_id', sa.CHAR(36), sa.ForeignKey('assessments.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), server_default='open'),
        sa.Column('domain_id', sa.String(50), nullable=True),
        sa.Column('domain_name', sa.String(100), nullable=True),
        sa.Column('question_id', sa.String(20), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_findings_assessment_id', 'findings', ['assessment_id'])
    op.create_index('ix_findings_severity', 'findings', ['severity'])
    op.create_index('ix_findings_status', 'findings', ['status'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('findings')
    op.drop_table('scores')
    op.drop_table('answers')
    op.drop_table('assessments')
    op.drop_table('organizations')
