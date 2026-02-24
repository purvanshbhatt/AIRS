"""extend_pilot_requests_for_enterprise_program

Revision ID: 0010_extend_pilot_requests
Revises: 0009_add_analytics_flag
Create Date: 2026-02-21

Phase 6 (Enterprise Pilot Program):
Extends the pilot_requests table with additional fields to capture richer
enterprise-programme leads for GTM outreach:
  - contact_name      (String 255, nullable) — primary contact name
  - industry          (String 100, nullable) — cleaned industry vertical
  - company_size      (String 64,  nullable) — headcount band, e.g. "201-1000"
  - ai_usage_description (Text, nullable)    — free-text on current AI/security use

Existing rows receive NULL for all new columns (backward-compatible).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_extend_pilot_requests"
down_revision: str = "0009_add_analytics_flag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pilot_requests", sa.Column("contact_name", sa.String(255), nullable=True))
    op.add_column("pilot_requests", sa.Column("industry", sa.String(100), nullable=True))
    op.add_column("pilot_requests", sa.Column("company_size", sa.String(64), nullable=True))
    op.add_column("pilot_requests", sa.Column("ai_usage_description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("pilot_requests", "ai_usage_description")
    op.drop_column("pilot_requests", "company_size")
    op.drop_column("pilot_requests", "industry")
    op.drop_column("pilot_requests", "contact_name")
