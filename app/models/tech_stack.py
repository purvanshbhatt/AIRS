"""
Tech Stack Registry model — tracks component versions and lifecycle status.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class LtsStatus(str, enum.Enum):
    """Lifecycle support status."""
    LTS = "lts"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EOL = "eol"


class TechStackItem(Base):
    """Tech stack component — tracks version and lifecycle risk."""

    __tablename__ = "tech_stack_registry"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False, index=True)

    component_name = Column(String(255), nullable=False)   # e.g. "Python", "React", "Node.js"
    version = Column(String(50), nullable=True)             # e.g. "3.8", "18.2", "16.20"
    lts_status = Column(SQLEnum(LtsStatus), nullable=False, default=LtsStatus.ACTIVE)
    major_versions_behind = Column(Integer, nullable=False, default=0)
    category = Column(String(100), nullable=True)           # e.g. "Runtime", "Framework", "Database"
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="tech_stack_items")

    def __repr__(self):
        return f"<TechStackItem(id={self.id}, name={self.component_name}, version={self.version}, status={self.lts_status})>"
