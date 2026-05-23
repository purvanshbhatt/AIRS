"""
FrameworkMappingRegistry — Links findings to compliance framework controls.

Maps each finding to specific NIST AI RMF, MITRE ATLAS, and other
framework control IDs. This is the source of truth for which compliance
controls a given security finding satisfies or gaps.

Architectural Invariant: All mappings are static/deterministic.
No LLM involvement in framework resolution.
"""

import uuid
import enum

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class FrameworkMappingRegistry(Base):
    """Static registry linking findings to compliance framework control IDs.

    Design Rationale:
      - 1-to-many: A single finding may map to multiple framework controls
        (e.g., EDR coverage maps to both NIST DE.CM-1 and MITRE ATLAS TA0043).
      - UniqueConstraint prevents duplicate (finding_id, framework, control) tuples.
      - mapping_version enables versioned updates without breaking audit trails.
    """

    __tablename__ = "framework_mapping_registry"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    finding_id = Column(
        CHAR(36),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to the finding this mapping covers.",
    )

    # --- Framework control identifiers ---
    nist_csf_control_id = Column(
        String(50), nullable=True,
        comment="NIST CSF 2.0 control ID (e.g., 'DE.CM-1', 'PR.AA-5').",
    )
    nist_ai_rmf_control_id = Column(
        String(50), nullable=True,
        comment="NIST AI RMF control ID (e.g., 'MAP 1.1', 'MEASURE 2.3').",
    )
    mitre_atlas_tactic_id = Column(
        String(50), nullable=True,
        comment="MITRE ATLAS tactic/technique ID (e.g., 'AML.T0043').",
    )
    soc2_control_id = Column(
        String(50), nullable=True,
        comment="SOC 2 Trust Services Criteria ID (e.g., 'CC6.1').",
    )
    iso27001_control_id = Column(
        String(50), nullable=True,
        comment="ISO 27001:2022 control ID (e.g., 'A.8.7').",
    )

    # --- Versioning ---
    mapping_version = Column(
        String(20), nullable=False, default="1.0.0",
        comment="Semantic version of this mapping definition.",
    )

    # --- Timestamps ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- Constraints ---
    __table_args__ = (
        UniqueConstraint(
            "finding_id", "nist_csf_control_id", "nist_ai_rmf_control_id",
            "mitre_atlas_tactic_id", "soc2_control_id", "iso27001_control_id",
            "mapping_version",
            name="uq_framework_mapping_composite",
        ),
        Index("ix_fmr_nist_ai_rmf", "nist_ai_rmf_control_id"),
        Index("ix_fmr_mitre_atlas", "mitre_atlas_tactic_id"),
    )

    # --- Relationships ---
    finding = relationship("Finding", backref="framework_mappings")

    def __repr__(self):
        return (
            f"<FrameworkMappingRegistry(id={self.id}, finding={self.finding_id}, "
            f"nist_ai={self.nist_ai_rmf_control_id}, mitre={self.mitre_atlas_tactic_id})>"
        )
