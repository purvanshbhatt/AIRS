"""
Report model - Persistent report records with snapshot data.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Text
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Report(Base):
    """
    Report entity - represents a generated report for an assessment.
    
    Reports store a snapshot of the assessment data at generation time,
    ensuring report consistency even if the rubric or scoring changes later.
    """
    
    __tablename__ = "reports"
    
    # Primary key
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Tenant isolation
    owner_uid = Column(String(128), nullable=False, index=True)
    
    # Foreign keys (indexed for efficient queries)
    organization_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False, index=True)
    assessment_id = Column(CHAR(36), ForeignKey("assessments.id"), nullable=False, index=True)
    
    # Report metadata
    report_type = Column(String(50), nullable=False, default="executive_pdf")
    title = Column(String(255), nullable=False)
    
    # Storage reference (file path or URL to stored PDF)
    storage_path = Column(String(512), nullable=True)
    
    # Snapshot data - JSON string containing point-in-time assessment data
    # Includes: overall_score, domain_scores, findings, baseline, llm_metadata
    snapshot = Column(Text, nullable=False)
    
    # Cached values from snapshot for efficient querying
    overall_score = Column(Float, nullable=True)
    maturity_level = Column(Integer, nullable=True)
    maturity_name = Column(String(50), nullable=True)
    findings_count = Column(Integer, nullable=True, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="reports")
    assessment = relationship("Assessment", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, type={self.report_type}, assessment={self.assessment_id})>"
