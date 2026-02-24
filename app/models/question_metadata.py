"""
QuestionMetadata model – stores enriched per-question metadata.

The canonical data lives in ``app.core.question_catalog`` (config-driven).
This table exists so that metadata can be queried via SQL for reporting,
and so that future admin-UI updates can persist without code deploys.

Important: This table does NOT influence scoring.  Scoring is deterministic
and driven exclusively by ``rubric.py``.
"""

import uuid
import enum

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class MaturityLevel(str, enum.Enum):
    """Assessment maturity tier for a question."""
    BASIC = "basic"
    MANAGED = "managed"
    ADVANCED = "advanced"


class EffortLevel(str, enum.Enum):
    """Implementation effort required."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImpactLevel(str, enum.Enum):
    """Security-posture impact when addressed."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ControlFunction(str, enum.Enum):
    """NIST CSF 2.0 control function."""
    GOVERN = "govern"
    IDENTIFY = "identify"
    PROTECT = "protect"
    DETECT = "detect"
    RESPOND = "respond"
    RECOVER = "recover"


class QuestionMetadata(Base):
    """Persisted enrichment metadata for a rubric question."""

    __tablename__ = "question_metadata"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String(20), nullable=False, unique=True, index=True)

    # Framework alignment tags (e.g. ["NIST-CSF-DE.CM-3", "CIS-8.2"])
    framework_tags = Column(JSON, nullable=False, default=list)

    # Maturity / effort / impact classification
    maturity_level = Column(SQLEnum(MaturityLevel), nullable=False, default=MaturityLevel.BASIC)
    effort_level = Column(SQLEnum(EffortLevel), nullable=False, default=EffortLevel.MEDIUM)
    impact_level = Column(SQLEnum(ImpactLevel), nullable=False, default=ImpactLevel.MEDIUM)

    # NIST CSF 2.0 control function
    control_function = Column(SQLEnum(ControlFunction), nullable=False, default=ControlFunction.DETECT)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return (
            f"<QuestionMetadata(question_id={self.question_id}, "
            f"maturity={self.maturity_level}, control={self.control_function})>"
        )
