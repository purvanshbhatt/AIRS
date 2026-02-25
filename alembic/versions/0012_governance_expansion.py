"""governance_expansion_modules

Revision ID: 0007_governance_expansion
Revises: 0006_add_audit_and_pilot
Create Date: 2025-07-14

Adds:
- Governance profile columns to organizations table
- soc2_controls column to findings table
- audit_calendar table
- tech_stack_registry table
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0012_governance_expansion"
down_revision: str = "0011_merge_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Governance profile columns on organizations ──────────────
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(sa.Column("revenue_band", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("employee_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("geo_regions", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("processes_pii", sa.Boolean(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("processes_phi", sa.Boolean(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("processes_cardholder_data", sa.Boolean(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("handles_dod_data", sa.Boolean(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("uses_ai_in_production", sa.Boolean(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("government_contractor", sa.Boolean(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("financial_services", sa.Boolean(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("application_tier", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("sla_target", sa.Float(), nullable=True))

    # ── SOC 2 controls on findings ───────────────────────────────
    with op.batch_alter_table("findings") as batch_op:
        batch_op.add_column(sa.Column("soc2_controls", sa.Text(), nullable=True))

    # ── Audit Calendar table ─────────────────────────────────────
    op.create_table(
        "audit_calendar",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("org_id", sa.CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("framework", sa.String(length=100), nullable=False),
        sa.Column("audit_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "audit_type",
            sa.Enum("external", "internal", name="audittype"),
            server_default="external",
            nullable=False,
        ),
        sa.Column("reminder_days_before", sa.Integer(), server_default="90", nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_calendar_org_id", "audit_calendar", ["org_id"])
    op.create_index("ix_audit_calendar_audit_date", "audit_calendar", ["audit_date"])

    # ── Tech Stack Registry table ────────────────────────────────
    op.create_table(
        "tech_stack_registry",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("org_id", sa.CHAR(36), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("component_name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column(
            "lts_status",
            sa.Enum("lts", "active", "deprecated", "eol", name="ltsstatus"),
            server_default="active",
            nullable=False,
        ),
        sa.Column("major_versions_behind", sa.Integer(), server_default="0", nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tech_stack_registry_org_id", "tech_stack_registry", ["org_id"])


def downgrade() -> None:
    op.drop_index("ix_tech_stack_registry_org_id", table_name="tech_stack_registry")
    op.drop_table("tech_stack_registry")

    op.drop_index("ix_audit_calendar_audit_date", table_name="audit_calendar")
    op.drop_index("ix_audit_calendar_org_id", table_name="audit_calendar")
    op.drop_table("audit_calendar")

    with op.batch_alter_table("findings") as batch_op:
        batch_op.drop_column("soc2_controls")

    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_column("sla_target")
        batch_op.drop_column("application_tier")
        batch_op.drop_column("financial_services")
        batch_op.drop_column("government_contractor")
        batch_op.drop_column("uses_ai_in_production")
        batch_op.drop_column("handles_dod_data")
        batch_op.drop_column("processes_cardholder_data")
        batch_op.drop_column("processes_phi")
        batch_op.drop_column("processes_pii")
        batch_op.drop_column("geo_regions")
        batch_op.drop_column("employee_count")
        batch_op.drop_column("revenue_band")
