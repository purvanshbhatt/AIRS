"""
Control Verification Engine Models
Deterministic storage of control verification states and evidence tracking.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class VerificationState(str, enum.Enum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    SELF_ATTESTED = "SELF_ATTESTED"
    NOT_VERIFIED = "NOT_VERIFIED"


class VerificationConfidence(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class VerificationResult(Base):
    """
    Stores the computed verification state of a control for an organization.
    This state is deterministically computed based on telemetry evidence.
    """
    __tablename__ = "verification_results"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    control_id = Column(String(100), nullable=False, index=True)
    state = Column(SQLEnum(VerificationState), default=VerificationState.NOT_VERIFIED, nullable=False)
    confidence_level = Column(SQLEnum(VerificationConfidence), default=VerificationConfidence.LOW, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization")
    evidence = relationship("ControlEvidence", back_populates="verification_result", cascade="all, delete-orphan")
    audit_logs = relationship("VerificationAuditLog", back_populates="verification_result", cascade="all, delete-orphan")


class ControlEvidence(Base):
    """
    Maps a specific telemetry event to a control verification result.
    """
    __tablename__ = "control_evidence"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_result_id = Column(CHAR(36), ForeignKey("verification_results.id", ondelete="CASCADE"), nullable=False, index=True)
    telemetry_event_id = Column(CHAR(36), ForeignKey("telemetry_events.id", ondelete="SET NULL"), nullable=True)
    connector_id = Column(CHAR(36), ForeignKey("connectors.id", ondelete="SET NULL"), nullable=True)
    
    # E.g., 'PASS', 'FAIL', 'NOT_APPLICABLE'
    status = Column(String(50), nullable=False)
    
    # Store arbitrary payload data for the evidence if telemetry_event_id is not enough
    evidence_payload = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    verification_result = relationship("VerificationResult", back_populates="evidence")


class VerificationAuditLog(Base):
    """
    Immutable audit log for every state transition in the Verification Engine.
    """
    __tablename__ = "verification_audit_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    verification_result_id = Column(CHAR(36), ForeignKey("verification_results.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_state = Column(SQLEnum(VerificationState), nullable=True)
    new_state = Column(SQLEnum(VerificationState), nullable=False)
    reason = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    verification_result = relationship("VerificationResult", back_populates="audit_logs")
