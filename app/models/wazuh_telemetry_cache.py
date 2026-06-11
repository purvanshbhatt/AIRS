"""
Wazuh Telemetry Cache model for caching manager status and vulnerabilities per organization.
"""

from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class WazuhTelemetryCache(Base):
    """Cached Wazuh telemetry data for multi-tenant isolation and polling isolation."""
    
    __tablename__ = "wazuh_telemetry_caches"
    
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True, index=True)
    agent_status = Column(Text, nullable=True)  # Serialized JSON string of agent status
    vulnerabilities = Column(Text, nullable=True)  # Serialized JSON string of CVE vulnerabilities
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<WazuhTelemetryCache(org_id={self.org_id}, updated_at={self.updated_at})>"
