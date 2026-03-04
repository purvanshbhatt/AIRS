"""
Pydantic schemas for Reliability Risk Index (RRI).
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


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


# ── New v2 Schemas ───────────────────────────────────────────────────

class BreachExposureBadgeSchema(BaseModel):
    """4-level executive breach exposure badge."""
    level: str = Field(..., description="within_budget / sla_strain / breach_high / contractual_risk")
    badge: str = Field(..., description="Emoji badge label")
    severity: str = Field(..., description="green / yellow / red / black")
    explanation: str


class AdvisoryItemSchema(BaseModel):
    """Deterministic architectural misalignment advisory."""
    severity: str = Field(..., description="critical / high / medium / info")
    title: str
    detail: str
    remediation: str


class ReliabilityConfidenceScoreSchema(BaseModel):
    """Reliability Confidence Score (RCS) — 2nd axis of resilience matrix."""
    total_score: float = Field(..., ge=0, le=100, description="0–100 confidence score")
    dr_test_recency: float = Field(..., ge=0, le=20)
    backup_validation: float = Field(..., ge=0, le=20)
    ir_tabletop_recency: float = Field(..., ge=0, le=20)
    monitoring_coverage: float = Field(..., ge=0, le=20)
    architecture_redundancy: float = Field(..., ge=0, le=20)
    confidence_band: str = Field(..., description="Verified / Moderate / Low / Unvalidated")
    sub_scores: Dict[str, float] = {}


class AutoRecommendationSchema(BaseModel):
    """Auto-recommendation when SLA/Tier is missing."""
    recommended_tier: str
    recommended_sla: float
    source: str = Field(..., description="industry / profile / default")
    rationale: str
    accept_action: str


class RRISnapshotSchema(BaseModel):
    """Point-in-time RRI snapshot for trend tracking."""
    org_id: str
    timestamp: str
    rri_score: float
    rcs_score: float
    risk_band: str
    confidence_band: str
    dimensions: Dict[str, float] = {}


# ── Main Responses ───────────────────────────────────────────────────

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
    # ── New v2 fields ────────────────────────────────────────────
    breach_exposure: Optional[BreachExposureBadgeSchema] = None
    advisories: List[AdvisoryItemSchema] = []
    reliability_confidence: Optional[ReliabilityConfidenceScoreSchema] = None
    auto_recommendation: Optional[AutoRecommendationSchema] = None


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


class AcceptRecommendationRequest(BaseModel):
    """Accept auto-detected tier/SLA recommendation."""
    recommended_tier: str
    recommended_sla: float
