import uuid
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from app.db.database import Base

class ReadinessSnapshot(Base):
    """Clinic readiness snapshot model."""
    __tablename__ = "readiness_snapshots"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date = Column(String(10), nullable=False)  # e.g. "2026-08-01"
    clinic_health_pct = Column(Integer, nullable=True)
    connector_health_pct = Column(Integer, nullable=True)
    status = Column(String(20), nullable=True)  # safe_to_open, action_needed, critical_risk
    checks_passed = Column(Integer, default=0)
    checks_failed = Column(Integer, default=0)
    checks_warning = Column(Integer, default=0)
    checks_unknown = Column(Integer, default=0)
    delta_reasons = Column(JSON, default=list)  # ["+ MFA enabled", "- Backup failed"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
