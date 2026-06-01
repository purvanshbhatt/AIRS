"""
SimulationResult — Adversarial Simulation Outcomes.

Records the results of adversarial attack simulations run against
AI assets. Each simulation targets a specific category (prompt injection,
data exfiltration, etc.) and produces blast radius scores, readiness
degradation metrics, and remediation recommendations.

Simulations may optionally target a specific AI asset and forecast
the impact on the organization's governance score.
"""

import uuid
import enum

from sqlalchemy import (
    Column, String, Float, DateTime, Text, Index,
    ForeignKey, Enum as SQLEnum, JSON,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func

from app.db.database import Base


class SimulationCategory(str, enum.Enum):
    """Categories of adversarial attack simulations."""
    prompt_injection = "prompt_injection"
    data_exfiltration = "data_exfiltration"
    rag_poisoning = "rag_poisoning"
    agent_privilege_escalation = "agent_privilege_escalation"
    model_dos = "model_dos"
    shadow_ai = "shadow_ai"
    sensitive_data_leakage = "sensitive_data_leakage"
    reliability_outage = "reliability_outage"
    malicious_payload_bypass = "malicious_payload_bypass"


class SimulationResult(Base):
    """Outcome of an adversarial attack simulation.

    Design Rationale:
      - attack_chain is a JSON array describing the simulated attack steps.
      - blast_radius_score quantifies the scope of potential damage (0-100).
      - readiness_degradation_pct measures governance score impact.
      - remediation_hooks provides actionable automation entry points.
      - score_impact_forecast predicts the effect on GHI if unmitigated.
    """

    __tablename__ = "simulation_results"

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
        comment="FK to the organization this simulation belongs to.",
    )
    category = Column(
        SQLEnum(SimulationCategory),
        nullable=False,
        comment="Category of the adversarial attack simulated.",
    )
    target_asset_id = Column(
        CHAR(36),
        ForeignKey("ai_assets.id", ondelete="CASCADE"),
        nullable=True,
        comment="FK to the AI asset targeted by the simulation (optional).",
    )
    attack_chain = Column(
        JSON,
        nullable=True,
        comment="JSON array of attack steps in the simulated chain.",
    )
    affected_controls = Column(
        JSON,
        nullable=True,
        comment="JSON array of control IDs affected by the simulation.",
    )
    blast_radius_score = Column(
        Float,
        nullable=False,
        comment="Blast radius score quantifying scope of damage (0-100).",
    )
    readiness_degradation_pct = Column(
        Float,
        nullable=False,
        comment="Percentage degradation in governance readiness score.",
    )
    business_impact_narrative = Column(
        Text,
        nullable=True,
        comment="Human-readable narrative of the business impact.",
    )
    remediation_hooks = Column(
        JSON,
        nullable=True,
        comment="JSON array of actionable remediation automation hooks.",
    )
    score_impact_forecast = Column(
        JSON,
        nullable=True,
        comment="JSON forecast of GHI score impact if unmitigated.",
    )
    executed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="UTC timestamp of when the simulation was executed.",
    )
    executed_by = Column(
        String(255),
        nullable=True,
        comment="UID of the actor or system that executed the simulation.",
    )

    __table_args__ = (
        Index("ix_simulation_org_category", "org_id", "category"),
        Index("ix_simulation_org_executed", "org_id", "executed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<SimulationResult(id={self.id}, category={self.category}, "
            f"blast_radius={self.blast_radius_score})>"
        )
