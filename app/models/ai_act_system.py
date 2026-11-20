"""
An AI system an organisation uses or supplies, recorded for the EU AI Act.

Only what the owner typed is stored: a name, what the system is for, the
supplier, the organisation's role, and the answers to the questionnaire. The
risk class is worked out from the answers each time it is read (see
``app.services.governance.eu_ai_act``), so it can never go stale against the
rules. ``obligation_status`` holds the owner's own statement per duty; ResilAI
does not verify it.
"""

import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class AIActSystem(Base):
    __tablename__ = "ai_act_systems"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(64), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    purpose = Column(Text, nullable=False)
    vendor = Column(String(120), nullable=True)
    role = Column(String(20), nullable=False)
    answers = Column(Text, nullable=False, default="{}")            # JSON object: answer key -> bool
    obligation_status = Column(Text, nullable=False, default="{}")  # JSON object: duty id -> status
    created_by = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
