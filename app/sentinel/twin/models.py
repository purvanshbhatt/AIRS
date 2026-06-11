"""
Digital Twin Simulation model - Stores outcomes from twin simulation runs.
"""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, JSON, Index
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.sql import func
from app.db.database import Base

class SentinelSimulation(Base):
    """
    Execution result of a Digital Twin simulation.
    Captures the impact of incidents given the current readiness posture.
    """
    
    __tablename__ = "sentinel_simulations"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(CHAR(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Simulation Details
    scenario_type = Column(String(255), nullable=False) # e.g., "Ransomware", "Data Exfiltration"
    status = Column(String(50), nullable=False, default="completed")
    
    # Calculated Outcomes (Deterministic based on evidence)
    readiness_impact_score = Column(Float, nullable=False) # Impacted score (0-100)
    
    # Weaknesses & Missing Controls (stored as JSON arrays/dicts)
    weaknesses = Column(JSON, nullable=True) # Likely failure points
    missing_controls = Column(JSON, nullable=True) # Mapped gaps
    
    # Raw simulation output logic context (for LLM to explain)
    simulation_context = Column(JSON, nullable=True)
    
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_simulation_org", "org_id"),
        Index("ix_simulation_scenario", "scenario_type"),
    )

    def __repr__(self):
        return f"<SentinelSimulation(id={self.id}, org_id={self.org_id}, scenario={self.scenario_type})>"
