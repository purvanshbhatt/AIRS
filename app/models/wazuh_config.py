"""
Wazuh Config model for storing SIEM lab credentials per organization.
"""

import uuid
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class WazuhConfig(Base):
    """Wazuh SIEM configuration for an organization."""
    
    __tablename__ = "wazuh_configs"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    wazuh_host = Column(String(255), nullable=False)
    wazuh_port = Column(Integer, nullable=False, default=55000)
    wazuh_api_key = Column(String(255), nullable=False)
    verify_ssl = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<WazuhConfig(id={self.id}, org_id={self.org_id}, host={self.wazuh_host})>"
