"""merge for v2 reports

Revision ID: 01c8a208e094
Revises: 27c4c8025899, a3c8e5f91b42
Create Date: 2026-09-01 15:10:02.235984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01c8a208e094'
down_revision: Union[str, Sequence[str], None] = ('27c4c8025899', 'a3c8e5f91b42')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
