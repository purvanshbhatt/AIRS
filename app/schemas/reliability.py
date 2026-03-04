"""
Pydantic schemas for Reliability Risk Index (RRI).
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class RRIDimensionSchema(BaseModel):
    """Single RRI dimension score."""
    name: str
    key: str
    score: float = Field(..., ge=0, le=100)
    weight: float
    weighted_score: float
    signals: List[str] = []
    gaps: List[str] = []


class DowntimeBudgetSchema(BaseModel):
    """Downtime budget derived from SLA target."""
    sla_target: float
    annual_minutes: float
    monthly_minutes: float
    annual_display: str
    monthly_display: str


class SLAAdvisorSchema(BaseModel):
    """Smart SLA Advisor recommendation."""
    recommended_tier: str
    sla_range: List[float]
    rationale: str
    industry: str
    confidence: str  # "high", "medium", "low"


class RRIResponse(BaseModel):
    """Full Reliability Risk Index response."""
    rri_score: float = Field(..., ge=0, le=100, description="Reliability exposure score (0=no risk, 100=maximum risk)")
    risk_band: str = Field(..., description="Low / Moderate / High / Critical")
    breach_probability: str = Field(..., description="Negligible / Low / Moderate / High")
    application_tier: str
    tier_multiplier: float
    raw_score: float
    downtime_budget: Optional[DowntimeBudgetSchema] = None
    dimensions: List[RRIDimensionSchema] = []
    top_gaps: List[str] = []
    architecture_alignment: str  # "aligned", "partial", "high_risk"
    sla_advisor: Optional[SLAAdvisorSchema] = None


class BreachSimulationRequest(BaseModel):
    """Board Simulation Mode: simulate SLA change."""
    simulated_sla: float = Field(..., gt=0, lt=100, description="Target SLA to simulate (e.g. 99.99)")


class BreachSimulationResponse(BaseModel):
    """Board Simulation Mode result."""
    current_sla: float
    simulated_sla: float
    current_budget: DowntimeBudgetSchema
    simulated_budget: DowntimeBudgetSchema
    required_improvements: List[str] = []
    control_gaps: List[str] = []
    readiness_delta: float  # Change in RRI score
    cost_impact: str
