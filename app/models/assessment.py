"""
Assessment model.
"""

import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class AssessmentStatus(str, enum.Enum):
    """Assessment status enum."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Assessment(Base):
    """Assessment entity - represents a single readiness assessment for an organization."""
    
    __tablename__ = "assessments"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False)
    owner_uid = Column(String(128), nullable=True, index=True)  # Firebase user UID for tenant isolation
    
    # Metadata
    version = Column(String(20), default="1.0.0")
    status = Column(SQLEnum(AssessmentStatus), default=AssessmentStatus.DRAFT)
    title = Column(String(255), nullable=True)
    
    # Schema versioning: 1=legacy numeric answers, 2=maturity-tier answers (v2.0)
    schema_version = Column(Integer, nullable=False, default=1, server_default="1")

    # Scoring results (populated after scoring)
    overall_score = Column(Float, nullable=True)
    maturity_level = Column(Integer, nullable=True)
    maturity_name = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="assessments")
    answers = relationship("Answer", back_populates="assessment", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="assessment", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="assessment", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="assessment", cascade="all, delete-orphan")
    roadmap_items = relationship("RoadmapItem", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Assessment(id={self.id}, org={self.organization_id}, score={self.overall_score})>"
