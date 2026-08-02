import uuid
from sqlalchemy import Column, DateTime, Integer, Float, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from app.db.database import Base

class ClinicValueMetric(Base):
    """Clinic value metric model."""
    __tablename__ = "clinic_value_metrics"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_date = Column(DateTime(timezone=True), nullable=False)
    accounts_protected = Column(Integer, default=0)
    backups_verified = Column(Integer, default=0)
    devices_protected = Column(Integer, default=0)
    problems_prevented = Column(Integer, default=0)
    estimated_downtime_avoided_hours = Column(Float, default=0.0)
    estimated_hipaa_records_protected = Column(Integer, default=0)
    estimated_time_saved_minutes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
