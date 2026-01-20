"""
Answer model - stores responses to assessment questions.
"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Answer(Base):
    """Answer entity - stores a single answer to a rubric question."""
    
    __tablename__ = "answers"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(CHAR(36), ForeignKey("assessments.id"), nullable=False)
    
    # Question reference (matches rubric question IDs like "tl_01", "dc_02", etc.)
    question_id = Column(String(20), nullable=False)
    
    # Answer value stored as string (converted during scoring)
    # Boolean: "true"/"false", Numeric: "90", "365", etc.
    value = Column(String(255), nullable=False)
    
    # Optional notes/context for the answer
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assessment = relationship("Assessment", back_populates="answers")
    
    def __repr__(self):
        return f"<Answer(id={self.id}, question={self.question_id}, value={self.value})>"
    
    def get_typed_value(self):
        """Convert string value to appropriate Python type."""
        if self.value.lower() in ("true", "yes", "1"):
            return True
        if self.value.lower() in ("false", "no", "0"):
            return False
        try:
            # Try numeric
            if "." in self.value:
                return float(self.value)
            return int(self.value)
        except ValueError:
            return self.value
