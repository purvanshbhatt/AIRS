"""Webhook model for outbound event delivery."""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Webhook(Base):
    """Organization-scoped webhook destinations."""

    __tablename__ = "webhooks"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False, index=True)

    url = Column(String(1024), nullable=False)
    # JSON-encoded list, e.g. ["assessment.scored"]
    event_types = Column(Text, nullable=False, default='["assessment.scored"]')
    secret = Column(String(255), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="webhooks")

    def __repr__(self):
        return f"<Webhook(id={self.id}, org={self.org_id}, active={self.is_active})>"