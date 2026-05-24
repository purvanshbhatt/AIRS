"""
Score Audit Log model for Deterministic Observability.
"""

import uuid

from sqlalchemy import Column, DateTime, Float, String, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ScoreAuditLog(Base):
    """Event-sourced audit log for GHI score changes.
    
    Provides 'forensic proof' of exactly when and why a score changed.
    """

    __tablename__ = "score_audit_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(CHAR(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    
    previous_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    
    trigger_event = Column(String(255), nullable=False, comment="What triggered the score change (e.g., 'siem_provenance_update').")
    affected_finding_ids = Column(JSON, nullable=True, comment="JSON list of finding IDs that influenced this score change.")
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    assessment = relationship("Assessment", backref="score_audit_logs")
    organization = relationship("Organization", backref="score_audit_logs")

    def __repr__(self):
        return f"<ScoreAuditLog(id={self.id}, assessment={self.assessment_id}, new_score={self.new_score})>"
