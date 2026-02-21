"""
Finding model - stores identified gaps and recommendations.
"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class Severity(str, enum.Enum):
    """Finding severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, enum.Enum):
    """Finding status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"  # Risk accepted


class Finding(Base):
    """Finding entity - represents a gap or issue identified during assessment."""
    
    __tablename__ = "findings"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(CHAR(36), ForeignKey("assessments.id"), nullable=False)
    
    # Finding details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(Severity), nullable=False)
    status = Column(SQLEnum(FindingStatus), default=FindingStatus.OPEN)
    
    # Context
    domain_id = Column(String(50), nullable=True)
    domain_name = Column(String(100), nullable=True)
    question_id = Column(String(20), nullable=True)
    
    # Evidence and remediation
    evidence = Column(Text, nullable=True)  # What was observed
    recommendation = Column(Text, nullable=True)  # How to fix
    
    # Priority for remediation (1 = highest)
    priority = Column(String(10), nullable=True)

    # NIST CSF 2.0 mapping (added v2.0)
    nist_function = Column(String(10), nullable=True)   # e.g. "DE", "PR", "RC"
    nist_category = Column(String(20), nullable=True)   # e.g. "DE.CM-1", "PR.AA-5"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assessment = relationship("Assessment", back_populates="findings")
    
    def __repr__(self):
        return f"<Finding(id={self.id}, title={self.title}, severity={self.severity})>"
