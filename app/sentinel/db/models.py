import uuid
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Index
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from app.sentinel.db.database import Base

class SentinelTelemetryEvent(Base):
    """
    Isolated local copy of a Telemetry Event inside the Sentinel Microservice.
    """
    __tablename__ = "sentinel_telemetry_events"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), nullable=False)
    
    source_system = Column(String(255), nullable=False)
    source_event_id = Column(String(255), nullable=True)
    
    event_type = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=True)
    
    payload = Column(JSON, nullable=True)
    
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_sentinel_telemetry_org", "org_id"),
        Index("ix_sentinel_telemetry_status", "processed"),
    )
