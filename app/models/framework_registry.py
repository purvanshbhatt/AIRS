"""
Framework Registry model — canonical compliance framework definitions.

Normalizes framework references across the platform via a proper database
table instead of hardcoded strings. Enables FK-based linking from findings,
audit calendar entries, and compliance engine outputs.
"""

import uuid
import enum
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from app.db.database import Base


class FrameworkCategory(str, enum.Enum):
    """Framework classification category."""
    REGULATORY = "regulatory"
    CONTRACTUAL = "contractual"
    VOLUNTARY = "voluntary"


class FrameworkRegistry(Base):
    """Canonical compliance framework registry."""

    __tablename__ = "framework_registry"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    category = Column(
        SQLEnum(FrameworkCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    version = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    reference_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
