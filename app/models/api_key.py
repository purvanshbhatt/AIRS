"""API key model for external integrations."""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class ApiKey(Base):
    """Stores hashed API keys for org-scoped external access."""

    __tablename__ = "api_keys"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_org_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False, index=True)

    # Store only derived key material
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    prefix = Column(String(32), nullable=False, index=True)

    # JSON-encoded scopes list, e.g. ["scores:read"]
    scopes = Column(Text, nullable=False, default='["scores:read"]')

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    organization = relationship("Organization", back_populates="api_keys")

    def __repr__(self):
        return f"<ApiKey(id={self.id}, org={self.owner_org_id}, active={self.is_active})>"