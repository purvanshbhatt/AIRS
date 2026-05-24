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

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, Index, Enum
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class FrameworkType(str, enum.Enum):
    """Supported compliance and governance frameworks."""
    NIST_CSF = "NIST_CSF"
    NIST_AI_RMF = "NIST_AI_RMF"
    ISO_42001 = "ISO_42001"
    MITRE_ATLAS = "MITRE_ATLAS"
    OWASP_LLM = "OWASP_LLM"
    SOC2 = "SOC2"
    ISO_27001 = "ISO_27001"


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

    framework_type = Column(
        Enum(FrameworkType),
        nullable=False,
        index=True,
        comment="The specific framework this mapping targets (e.g., NIST_AI_RMF).",
    )
    
    control_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="The control identifier within the framework (e.g., 'MAP 1.1', 'DE.CM-1').",
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
            "finding_id", "framework_type", "control_id", "mapping_version",
            name="uq_framework_mapping_dynamic",
        ),
    )

    # --- Relationships ---
    finding = relationship("Finding", backref="framework_mappings")

    def __repr__(self):
        return (
            f"<FrameworkMappingRegistry(id={self.id}, finding={self.finding_id}, "
            f"framework={self.framework_type.value}, control={self.control_id})>"
        )
