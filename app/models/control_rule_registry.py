"""
ControlRuleRegistry — Static Rule-to-Framework Compliance Lookup Table.

Maps deterministic finding rule IDs (e.g. 'DC-001') directly to compliance
framework controls (NIST AI RMF, MITRE ATLAS). This is the source-of-truth
for resolving SIEM telemetry against the governance framework.

Architectural Invariant:
  - Mappings are code-defined and seeded via Alembic data migrations.
  - NO LLM involvement in rule resolution.
  - 100% deterministic lookup by (finding_rule_id, mapping_version).

Distinct from FrameworkMappingRegistry which links DB finding FK rows;
this table operates at the static rule definition layer.
"""

import uuid
import enum

import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class ControlRuleRegistry(Base):
    """Static registry mapping finding rule IDs to compliance framework controls.

    Design Rationale:
      - Indexed by finding_rule_id (e.g. 'DC-001'), not a Finding FK.
      - A single rule can map to multiple frameworks via separate rows.
      - mapping_version enables versioned rollouts without breaking audit trails.
      - is_active enables soft-deprecation of outdated mappings.
      - Composite unique constraint prevents duplicate (rule, version) entries.
    """

    __tablename__ = "control_rule_registry"

    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Surrogate UUID primary key.",
    )

    # ── Rule Identification ─────────────────────────────────────────────────
    finding_rule_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Deterministic rule identifier (e.g. 'DC-001', 'IV-002'). "
                "Matches the rule_id used by the FindingsEngine and SIEM forwarder.",
    )

    # ── Compliance Framework Control IDs ───────────────────────────────────
    nist_ai_rmf_control_id = Column(
        String(50),
        nullable=True,
        comment="NIST AI RMF control identifier (e.g. 'GOVERN-1.1', 'MAP-1.5').",
    )
    mitre_atlas_tactic_id = Column(
        String(50),
        nullable=True,
        comment="MITRE ATLAS tactic/technique ID (e.g. 'AML.TA0001', 'AML.T0043').",
    )

    # ── Versioning ─────────────────────────────────────────────────────────
    mapping_version = Column(
        String(20),
        nullable=False,
        default="2026.1",
        server_default="2026.1",
        comment="Semantic version of this mapping definition (e.g. '2026.1').",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="Soft-delete flag. Inactive mappings are excluded from resolution.",
    )

    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Constraints ────────────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "finding_rule_id",
            "mapping_version",
            name="uq_control_rule_rule_version",
        ),
        Index(
            "ix_control_rule_active_rule",
            "finding_rule_id",
            "is_active",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ControlRuleRegistry(rule={self.finding_rule_id!r}, "
            f"nist={self.nist_ai_rmf_control_id!r}, "
            f"atlas={self.mitre_atlas_tactic_id!r}, "
            f"version={self.mapping_version!r}, active={self.is_active})>"
        )
