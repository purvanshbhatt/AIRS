"""merge_heads_before_governance

Revision ID: 0011_merge_heads
Revises: 0010_extend_pilot_requests, 0007_add_question_metadata
Create Date: 2026-02-24

Merge migration: unifies the three branches that diverged from 0006
into a single timeline before governance expansion modules.

Branches merged:
  - 0006 → 0007_add_nist → 0008 → 0009 → 0010_extend_pilot_requests
  - 0006 → 0007_add_question_metadata
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0011_merge_heads"
down_revision: tuple = ("0010_extend_pilot_requests", "0007_add_question_metadata")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge-only migration — no schema changes."""
    pass


def downgrade() -> None:
    """Merge-only migration — no schema changes."""
    pass
