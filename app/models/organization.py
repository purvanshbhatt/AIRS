"""
Organization model.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Organization(Base):
    """Organization entity."""
    
    __tablename__ = "organizations"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_uid = Column(String(128), nullable=True, index=True)  # Firebase user UID for tenant isolation
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)  # e.g., "1-50", "51-200", "201-1000", "1000+"
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    integration_status = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assessments = relationship("Assessment", back_populates="organization", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    external_findings = relationship("ExternalFinding", back_populates="organization", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, owner={self.owner_uid})>"
