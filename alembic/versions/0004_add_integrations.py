"""add_api_keys_webhooks_and_roadmap_items

Revision ID: 0004_add_integrations
Revises: 0003_add_reports
Create Date: 2026-02-14

Adds integration primitives:
- api_keys for headless pull integrations
- webhooks for push integrations
- roadmap_items for roadmap tracker persistence
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_add_integrations'
down_revision: str = '0003_add_reports'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('owner_org_id', sa.CHAR(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('key_hash', sa.String(128), nullable=False),
        sa.Column('prefix', sa.String(32), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=False, server_default='["scores:read"]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index('ix_api_keys_owner_org_id', 'api_keys', ['owner_org_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    op.create_index('ix_api_keys_prefix', 'api_keys', ['prefix'])

    op.create_table(
        'webhooks',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('org_id', sa.CHAR(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('url', sa.String(1024), nullable=False),
        sa.Column('event_types', sa.Text(), nullable=False, server_default='["assessment.scored"]'),
        sa.Column('secret', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_webhooks_org_id', 'webhooks', ['org_id'])

    op.create_table(
        'roadmap_items',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('assessment_id', sa.CHAR(36), sa.ForeignKey('assessments.id'), nullable=False),
        sa.Column('owner_uid', sa.String(128), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('phase', sa.String(8), nullable=False, server_default='30'),
        sa.Column('status', sa.String(32), nullable=False, server_default='not_started'),
        sa.Column('priority', sa.String(16), nullable=False, server_default='medium'),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('effort', sa.String(32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_roadmap_items_assessment_id', 'roadmap_items', ['assessment_id'])
    op.create_index('ix_roadmap_items_owner_uid', 'roadmap_items', ['owner_uid'])


def downgrade() -> None:
    op.drop_index('ix_roadmap_items_owner_uid', table_name='roadmap_items')
    op.drop_index('ix_roadmap_items_assessment_id', table_name='roadmap_items')
    op.drop_table('roadmap_items')

    op.drop_index('ix_webhooks_org_id', table_name='webhooks')
    op.drop_table('webhooks')

    op.drop_index('ix_api_keys_prefix', table_name='api_keys')
    op.drop_index('ix_api_keys_key_hash', table_name='api_keys')
    op.drop_index('ix_api_keys_owner_org_id', table_name='api_keys')
    op.drop_table('api_keys')