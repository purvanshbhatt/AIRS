"""Roadmap tracker item model."""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class RoadmapItem(Base):
    """User-managed roadmap tracking items for an assessment."""

    __tablename__ = "roadmap_items"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(CHAR(36), ForeignKey("assessments.id"), nullable=False, index=True)
    owner_uid = Column(String(128), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    phase = Column(String(8), nullable=False, default="30")
    status = Column(String(32), nullable=False, default="not_started")
    priority = Column(String(16), nullable=False, default="medium")
    owner = Column(String(255), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    effort = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    assessment = relationship("Assessment", back_populates="roadmap_items")

    def __repr__(self):
        return f"<RoadmapItem(id={self.id}, assessment={self.assessment_id}, status={self.status})>"