"""Audit event model for organization-level activity logs."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class AuditEvent(Base):
    """Organization-scoped immutable audit log event."""

    __tablename__ = "audit_events"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False, index=True)
    action = Column(String(128), nullable=False, index=True)
    actor = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    organization = relationship("Organization", back_populates="audit_events")

    def __repr__(self):
        return f"<AuditEvent(id={self.id}, org={self.org_id}, action={self.action})>"

