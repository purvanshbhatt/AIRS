from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum, JSON
from sqlalchemy.sql import func
from app.models.base import Base
import enum

class MomentStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED_AUTOMATICALLY = "resolved_automatically"
    RESOLVED_MANUALLY = "resolved_manually"
    EXPIRED = "expired"

class ClinicMomentRecord(Base):
    """
    Persistent storage for Clinic Moments.
    This acts as the backend repository, retaining all internal identifiers
    and remediation logic which are NEVER exposed to the frontend.
    """
    __tablename__ = "clinic_moments"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, index=True, nullable=False)
    
    question_id = Column(String, nullable=False, index=True)
    capability_id = Column(String, nullable=False, index=True)
    
    verdict = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    severity = Column(String, nullable=False, default="medium")
    
    # JSON column containing human-readable translations
    translation = Column(JSON, nullable=False)
    
    # JSON column containing action intents and automation params (backend ONLY)
    actions = Column(JSON, nullable=False, default=list)
    
    # JSON column containing source telemetry IDs that triggered this moment
    evidence_ids = Column(JSON, nullable=False, default=list)
    
    status = Column(SAEnum(MomentStatus), default=MomentStatus.ACTIVE, nullable=False, index=True)
    
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True) # E.g., next morning check
    
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True) # User ID or 'system'
    
    # Audit log of executions on this moment
    execution_history = Column(JSON, nullable=False, default=list)
