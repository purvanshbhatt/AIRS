"""
Roadmap item model.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from app.db.database import Base
import uuid

class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), ForeignKey("organizations.id"), nullable=False)
    assessment_id = Column(CHAR(36), ForeignKey("assessments.id"), nullable=True) # Optional link to source
    owner_uid = Column(String(128), index=True) 

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="todo") # todo, in_progress, done
    priority = Column(String(50), default="medium") # high, medium, low
    effort = Column(String(50), default="medium") # high, medium, low
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
