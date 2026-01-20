"""
Score model - stores domain scores for an assessment.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Score(Base):
    """Score entity - stores a domain score for an assessment."""
    
    __tablename__ = "scores"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(CHAR(36), ForeignKey("assessments.id"), nullable=False)
    
    # Domain identification
    domain_id = Column(String(50), nullable=False)  # e.g., "telemetry_logging"
    domain_name = Column(String(100), nullable=False)  # e.g., "Telemetry & Logging"
    
    # Score values
    score = Column(Float, nullable=False)  # 0-5 scale
    max_score = Column(Float, default=5.0)
    weight = Column(Float, nullable=False)  # Weight percentage (e.g., 25)
    weighted_score = Column(Float, nullable=False)  # Contribution to overall score
    
    # Raw points for reference
    raw_points = Column(Float, nullable=True)
    max_raw_points = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assessment = relationship("Assessment", back_populates="scores")
    
    def __repr__(self):
        return f"<Score(id={self.id}, domain={self.domain_id}, score={self.score})>"
