"""add_governance_engine_provenance

Creates the Trust Anchor architecture tables:
  - framework_mapping_registry: links findings to compliance framework controls
  - finding_provenance: immutable cryptographic provenance per finding

Revision ID: 0014
Revises: 0013_framework_registry
Create Date: 2026-05-23 05:15:00.000000+00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013_framework_registry'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- FrameworkMappingRegistry ---
    op.create_table(
        'framework_mapping_registry',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('finding_id', sa.CHAR(36), sa.ForeignKey('findings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('nist_csf_control_id', sa.String(50), nullable=True),
        sa.Column('nist_ai_rmf_control_id', sa.String(50), nullable=True),
        sa.Column('mitre_atlas_tactic_id', sa.String(50), nullable=True),
        sa.Column('soc2_control_id', sa.String(50), nullable=True),
        sa.Column('iso27001_control_id', sa.String(50), nullable=True),
        sa.Column('mapping_version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_fmr_finding_id', 'framework_mapping_registry', ['finding_id'])
    op.create_index('ix_fmr_nist_ai_rmf', 'framework_mapping_registry', ['nist_ai_rmf_control_id'])
    op.create_index('ix_fmr_mitre_atlas', 'framework_mapping_registry', ['mitre_atlas_tactic_id'])

    # Composite unique constraint to prevent duplicate mappings
    op.create_unique_constraint(
        'uq_framework_mapping_composite',
        'framework_mapping_registry',
        ['finding_id', 'nist_csf_control_id', 'nist_ai_rmf_control_id',
         'mitre_atlas_tactic_id', 'soc2_control_id', 'iso27001_control_id',
         'mapping_version'],
    )

    # --- FindingProvenance (Trust Anchor) ---
    op.create_table(
        'finding_provenance',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('finding_id', sa.CHAR(36), sa.ForeignKey('findings.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('siem_alert_id', sa.String(255), nullable=True),
        sa.Column('evidence_hash', sa.String(64), nullable=False),
        sa.Column('evidence_payload_ref', sa.Text(), nullable=True),
        sa.Column('verification_source', sa.Enum(
            'SIEM_WAZUH', 'SIEM_SPLUNK', 'SIEM_ELASTIC', 'MANUAL_AUDIT', 'SELF_ATTESTED',
            name='verificationsource',
        ), nullable=False, server_default='SELF_ATTESTED'),
        sa.Column('verification_status', sa.Enum(
            'SOC_VERIFIED', 'PROVISIONAL', 'CONTRADICTED',
            name='provenancestatus',
        ), nullable=False, server_default='PROVISIONAL'),
        sa.Column('rule_id_matched', sa.String(50), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('verified_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_provenance_finding_id', 'finding_provenance', ['finding_id'], unique=True)
    op.create_index('ix_provenance_siem_alert_id', 'finding_provenance', ['siem_alert_id'])


def downgrade() -> None:
    op.drop_table('finding_provenance')
    op.drop_table('framework_mapping_registry')
    # Drop enums for PostgreSQL
    op.execute("DROP TYPE IF EXISTS verificationsource")
    op.execute("DROP TYPE IF EXISTS provenancestatus")
