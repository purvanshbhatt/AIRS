import uuid
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class EvidenceLedger(Base):
    """
    Immutable Evidence Ledger.
    Every piece of evidence collected by any adapter is hashed and stored here permanently.
    This creates the unbreakable chain of custody for Readiness Scores.
    """
    __tablename__ = "evidence_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    connector_id = Column(String(36), ForeignKey("connectors.id"), nullable=True)
    
    evidence_hash = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    source_name = Column(String, nullable=False) # e.g. "Splunk", "CrowdStrike"
    event_type = Column(String, nullable=False)
    raw_payload = Column(JSON, nullable=False)
    
    # Confidence Metrics (Snapshot at collection)
    confidence_freshness = Column(Integer, default=100)
    confidence_completeness = Column(Integer, default=100)
    confidence_integrity = Column(Integer, default=100)
    confidence_availability = Column(Integer, default=100)
    overall_confidence = Column(Integer, default=100)

    # Verification State
    verification_status = Column(String, default="pending", index=True) # pending, verified, rejected
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NormalizedEvidenceRecord(Base):
    """
    The active state representation of Evidence, used by the Verification Engine.
    Maps to the EvidenceLedger via evidence_hash.
    """
    __tablename__ = "normalized_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    
    evidence_hash = Column(String(64), ForeignKey("evidence_ledger.evidence_hash"), nullable=False, index=True)
    
    asset_id = Column(String(36), nullable=True, index=True)
    control_id = Column(String(36), nullable=True, index=True)
    
    severity = Column(String, nullable=False, default="info")
    processed = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ledger_entry = relationship("EvidenceLedger", foreign_keys=[evidence_hash], primaryjoin="EvidenceLedger.evidence_hash == NormalizedEvidenceRecord.evidence_hash")
