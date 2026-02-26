"""
Audit Calendar model — tracks upcoming audits and review dates.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class AuditType(str, enum.Enum):
    """Audit type classification."""
    EXTERNAL = "external"
    INTERNAL = "internal"


class AuditCalendarEntry(Base):
    """Audit calendar entry — represents a scheduled or planned audit."""

    __tablename__ = "audit_calendar"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False, index=True)

    framework = Column(String(100), nullable=False)        # e.g. "SOC 2", "HIPAA", "PCI-DSS"
    audit_date = Column(DateTime(timezone=True), nullable=False)
    audit_type = Column(SQLEnum(AuditType), nullable=False, default=AuditType.EXTERNAL)
    reminder_days_before = Column(Integer, nullable=False, default=90)
    notes = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="audit_calendar_entries")

    def __repr__(self):
        return f"<AuditCalendarEntry(id={self.id}, framework={self.framework}, date={self.audit_date})>"
