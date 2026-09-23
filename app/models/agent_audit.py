"""
Agent Audit model for 48-Hour Live AI Agent Blast-Radius Audit sessions.
"""

import uuid
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.sqlite import CHAR
from app.db.database import Base


class AgentAudit(Base):
    """48-Hour AI Agent Blast-Radius Audit Session."""

    __tablename__ = "agent_audits"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(128), nullable=False, index=True)
    created_by = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="CREATED")  # CREATED, INGESTING, EVALUATING, COMPLETE, INSUFFICIENT_EVIDENCE, EXPIRED
    audit_window = Column(String(16), nullable=False, default="48h")
    source_type = Column(String(32), nullable=False, default="splunk")  # splunk, multi_source, agent_trace, upload
    agent_name = Column(String(255), nullable=True, default="Customer Support Agent")
    environment = Column(String(64), nullable=True, default="Production")
    business_context = Column(Text, nullable=True)

    telemetry_event_count = Column(Integer, nullable=False, default=0)
    evidence_count = Column(Integer, nullable=False, default=0)
    agent_count = Column(Integer, nullable=False, default=1)
    tool_action_count = Column(Integer, nullable=False, default=0)
    verified_action_count = Column(Integer, nullable=False, default=0)
    unverified_action_count = Column(Integer, nullable=False, default=0)
    readiness_score = Column(Float, nullable=False, default=0.0)
    evidence_confidence = Column(String(32), nullable=False, default="UNVERIFIED")  # VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED

    findings = Column(Text, nullable=False, default="[]")  # JSON serialized findings
    framework_alignment = Column(Text, nullable=False, default="{}")  # JSON serialized framework mapping
    remediation_priorities = Column(Text, nullable=False, default="[]")  # JSON serialized remediation tasks

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(hours=48))
    completed_at = Column(DateTime, nullable=True)

    def is_expired(self) -> bool:
        """Check if 48-hour bounded observation window has expired."""
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    def to_dict(self) -> dict:
        """Serialize audit object to dictionary matching frontend contract."""
        return {
            "id": self.id,
            "org_id": self.org_id,
            "created_by": self.created_by or "system",
            "status": "EXPIRED" if (self.status != "COMPLETE" and self.is_expired()) else self.status,
            "audit_window": self.audit_window,
            "source_type": self.source_type,
            "agent_name": self.agent_name,
            "environment": self.environment,
            "business_context": self.business_context,
            "telemetry_event_count": self.telemetry_event_count,
            "evidence_count": self.evidence_count,
            "agent_count": self.agent_count,
            "tool_action_count": self.tool_action_count,
            "verified_action_count": self.verified_action_count,
            "unverified_action_count": self.unverified_action_count,
            "readiness_score": round(self.readiness_score, 1),
            "evidence_confidence": self.evidence_confidence,
            "findings": json.loads(self.findings) if isinstance(self.findings, str) else (self.findings or []),
            "framework_alignment": json.loads(self.framework_alignment) if isinstance(self.framework_alignment, str) else (self.framework_alignment or {}),
            "remediation_priorities": json.loads(self.remediation_priorities) if isinstance(self.remediation_priorities, str) else (self.remediation_priorities or []),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
