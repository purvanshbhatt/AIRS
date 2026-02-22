"""Pilot request model for Public Beta inbound leads."""

import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class PilotRequest(Base):
    """Inbound pilot request submission."""

    __tablename__ = "pilot_requests"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False)
    team_size = Column(String(64), nullable=False)
    current_security_tools = Column(Text, nullable=True)
    email = Column(String(255), nullable=False, index=True)
    # Enterprise Pilot Program extended fields (Phase 6 / migration 0010)
    contact_name = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    company_size = Column(String(64), nullable=True)
    ai_usage_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<PilotRequest(id={self.id}, company_name={self.company_name})>"

