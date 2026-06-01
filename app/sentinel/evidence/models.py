"""
Telemetry Evidence model - Stores deterministic evidence generated from raw telemetry.
"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Boolean, Index
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from app.db.database import Base

class TelemetryEvidence(Base):
    """
    Deterministic evidence mapped from raw telemetry.
    This evidence feeds into the existing ResilAI scoring engine.
    """
    
    __tablename__ = "telemetry_evidence"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Source Tracking
    source = Column(String(255), nullable=False) # e.g., "splunk"
    source_reference = Column(String(255), nullable=True) # Upstream incident/alert ID
    
    # Evidence categorization
    event_type = Column(String(255), nullable=False)
    evidence_type = Column(String(255), nullable=False) # e.g., "failed_backup_validation"
    severity = Column(String(50), nullable=False)
    
    # Details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Confidence and Validation
    confidence = Column(Float, nullable=False, default=1.0)
    telemetry_verified = Column(Boolean, nullable=False, default=True)
    
    # Mapping
    control_domain = Column(String(100), nullable=True)
    framework_mapping = Column(String(100), nullable=True)
    
    # Link back to raw event for traceability
    raw_event_reference = Column(
        CHAR(36), 
        ForeignKey("telemetry_events.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_evidence_type", "evidence_type"),
        Index("ix_evidence_source", "source"),
        Index("ix_evidence_domain", "control_domain"),
    )

    def __repr__(self):
        return f"<TelemetryEvidence(id={self.id}, type={self.evidence_type}, severity={self.severity})>"
