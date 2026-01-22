"""fix_enum_types

Revision ID: 0004
Revises: 0003_add_reports
Create Date: 2025-01-20

Fix enum column types for PostgreSQL compatibility.
The initial migration used String columns but SQLAlchemy models use SQLEnum,
causing type mismatches on PostgreSQL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_fix_enum_types'
down_revision: Union[str, Sequence[str], None] = '0003_add_reports'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert String enum columns to native PostgreSQL enum types.
    
    This ensures the SQLAlchemy model (which uses SQLEnum) matches the database schema.
    For SQLite, this is a no-op since SQLite doesn't have native enum support.
    """
    # Get the database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'postgresql':
        # Create enum types in PostgreSQL
        
        # Severity enum for findings
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE severity AS ENUM ('low', 'medium', 'high', 'critical');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # FindingStatus enum
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE findingstatus AS ENUM ('open', 'in_progress', 'resolved', 'accepted');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # AssessmentStatus enum (if not exists)
        op.execute("""
            DO $$ BEGIN
                CREATE TYPE assessmentstatus AS ENUM ('draft', 'in_progress', 'completed', 'archived');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Now alter the columns to use these enum types
        # For findings.severity: String -> severity enum
        op.execute("""
            ALTER TABLE findings 
            ALTER COLUMN severity TYPE severity 
            USING severity::severity;
        """)
        
        # For findings.status: String -> findingstatus enum
        op.execute("""
            ALTER TABLE findings 
            ALTER COLUMN status TYPE findingstatus 
            USING status::findingstatus;
        """)
        
        # Note: assessments.status is kept as String for backwards compatibility
        # since it's used with simple string values in many places
        
    # For SQLite, no changes needed - it stores enums as strings anyway


def downgrade() -> None:
    """Revert enum columns back to strings."""
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'postgresql':
        # Convert back to VARCHAR
        op.execute("""
            ALTER TABLE findings 
            ALTER COLUMN severity TYPE VARCHAR(20) 
            USING severity::text;
        """)
        
        op.execute("""
            ALTER TABLE findings 
            ALTER COLUMN status TYPE VARCHAR(20) 
            USING status::text;
        """)
        
        # Drop enum types
        op.execute("DROP TYPE IF EXISTS severity;")
        op.execute("DROP TYPE IF EXISTS findingstatus;")
        op.execute("DROP TYPE IF EXISTS assessmentstatus;")
