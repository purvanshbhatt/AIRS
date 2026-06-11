"""
GovernancePolicy — Policy Definition & Enforcement.

Manages organizational governance policies that gate AI usage, model
approvals, vendor risk, deployment, environment restrictions, and data
handling. Each policy carries a versioned JSON definition and an
enforcement mode (enforce, audit, disabled).

PolicyEvaluationLog provides an append-only audit trail of every
policy evaluation, recording context, result, and any violations.
"""

import uuid
import enum

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Index,
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class PolicyType(str, enum.Enum):
    """Categories of governance policies."""
    ai_usage = "ai_usage"
    model_approval = "model_approval"
    vendor_risk = "vendor_risk"
    deployment_gate = "deployment_gate"
    environment_restriction = "environment_restriction"
    data_handling = "data_handling"


class EnforcementMode(str, enum.Enum):
    """Enforcement mode for a governance policy."""
    enforce = "enforce"
    audit = "audit"
    disabled = "disabled"


class GovernancePolicy(Base):
    """Organizational governance policy definition.

    Design Rationale:
      - policy_definition is a versioned JSON schema defining the policy rules.
      - version enables policy evolution without breaking audit history.
      - enforcement_mode defaults to 'audit' for safe rollout.
      - is_active enables soft-deprecation without deletion.
    """

    __tablename__ = "governance_policies"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Surrogate UUID primary key.",
    )
    org_id = Column(
        CHAR(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the owning organization.",
    )
    name = Column(
        String(255),
        nullable=False,
        comment="Human-readable name of the governance policy.",
    )
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the policy's intent and scope.",
    )
    policy_type = Column(
        SQLEnum(PolicyType),
        nullable=False,
        comment="Category of this governance policy.",
    )
    policy_definition = Column(
        JSON,
        nullable=False,
        comment="Versioned JSON schema defining the policy rules.",
    )
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Policy version counter for audit trail.",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Soft-delete flag. Inactive policies are not evaluated.",
    )
    enforcement_mode = Column(
        SQLEnum(EnforcementMode),
        nullable=False,
        default=EnforcementMode.audit,
        comment="Enforcement mode: enforce, audit, or disabled.",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Row creation timestamp.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Row last-update timestamp.",
    )
    created_by = Column(
        String(255),
        nullable=True,
        comment="UID of the actor who created this policy.",
    )

    __table_args__ = (
        Index("ix_policy_org_type", "org_id", "policy_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<GovernancePolicy(id={self.id}, name={self.name!r}, "
            f"type={self.policy_type}, mode={self.enforcement_mode})>"
        )


class PolicyEvaluationLog(Base):
    """Append-only log of governance policy evaluations.

    Design Rationale:
      - evaluation_context is a JSON blob capturing what was being evaluated.
      - result is pass/fail/warn to allow ternary outcomes.
      - violations is a JSON array of specific rule violations found.
    """

    __tablename__ = "policy_evaluation_logs"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Surrogate UUID primary key.",
    )
    policy_id = Column(
        CHAR(36),
        ForeignKey("governance_policies.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the governance policy that was evaluated.",
    )
    org_id = Column(
        CHAR(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to the organization context of the evaluation.",
    )
    evaluation_context = Column(
        JSON,
        nullable=True,
        comment="JSON blob describing what triggered and was evaluated.",
    )
    result = Column(
        String(50),
        nullable=False,
        comment="Evaluation outcome: pass, fail, or warn.",
    )
    violations = Column(
        JSON,
        nullable=True,
        comment="JSON array of specific rule violations found.",
    )
    evaluated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="UTC timestamp of when the evaluation occurred.",
    )
    evaluated_by = Column(
        String(255),
        nullable=True,
        comment="UID of the actor or system that triggered the evaluation.",
    )

    __table_args__ = (
        Index("ix_policy_eval_policy_evaluated", "policy_id", "evaluated_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<PolicyEvaluationLog(id={self.id}, policy={self.policy_id}, "
            f"result={self.result!r})>"
        )
