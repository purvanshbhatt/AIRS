"""
Simulation Pydantic Schemas — Threat simulation request/response models.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SimulationRunRequest(BaseModel):
    """Launch an adversarial simulation against an AI asset."""
    category: str = Field(..., description="Simulation category (prompt_injection, data_exfiltration, malicious_payload_bypass, etc.)")
    target_asset_id: Optional[str] = Field(None, description="Target AI asset UUID (optional)")


class SimulationResultResponse(BaseModel):
    """Single simulation execution result."""
    id: str
    org_id: str
    category: str
    target_asset_id: Optional[str] = None
    attack_chain: List[Any] = Field(default_factory=list)
    affected_controls: List[str] = Field(default_factory=list)
    blast_radius_score: float
    readiness_degradation_pct: float
    business_impact_narrative: Optional[str] = None
    remediation_hooks: Optional[List[Any]] = None
    score_impact_forecast: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    executed_by: Optional[str] = None
    model_config = {"from_attributes": True}


class SimulationResultListResponse(BaseModel):
    """Paginated simulation result listing."""
    results: List[SimulationResultResponse]
    total: int


class FullAssessmentResponse(BaseModel):
    """Full threat assessment summary across all categories."""
    results: List[SimulationResultResponse]
    summary: Dict[str, Any] = Field(default_factory=dict, description="Aggregate metrics: total_simulations, avg_blast_radius, critical_findings, most_vulnerable_category")
