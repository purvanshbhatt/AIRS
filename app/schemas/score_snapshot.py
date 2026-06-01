"""
Score Snapshot Pydantic Schemas — Continuous scoring models.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScoreSnapshotResponse(BaseModel):
    """Point-in-time governance score snapshot."""
    id: str
    org_id: str
    snapshot_trigger: str
    overall_score: float
    ghi_score: float
    ghi_grade: str
    domain_scores: Dict[str, Any]
    framework_coverage: Optional[Dict[str, Any]] = None
    evidence_freshness_score: Optional[float] = None
    confidence_score: Optional[float] = None
    telemetry_weight: float = 0.0
    stale_penalty_applied: float = 0.0
    triggered_by: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ScoreTimelineResponse(BaseModel):
    """Chronological score history."""
    snapshots: List[ScoreSnapshotResponse]


class ContinuousScoreResponse(BaseModel):
    """Live continuous governance score with full calculation breakdown."""
    current_score: float = Field(..., description="Current composite governance readiness score")
    ghi_score: float = Field(..., description="Governance Health Index")
    ghi_grade: str = Field(..., description="Letter grade (A+, A, B, etc.)")
    confidence: float = Field(..., description="Data completeness confidence (0.0-1.0)")
    evidence_freshness: float = Field(..., description="Evidence freshness score")
    telemetry_bonus: float = Field(..., description="Points added from live telemetry")
    stale_penalty: float = Field(..., description="Points deducted for stale evidence (0-10, floored at static baseline)")
    domain_scores: Dict[str, Any] = Field(default_factory=dict)
    framework_coverage: Dict[str, Any] = Field(default_factory=dict)
    last_assessment_age_days: int = 0
    active_connectors: int = 0
    score_components: Dict[str, Any] = Field(default_factory=dict, description="Detailed calculation breakdown")


class ScoreDriftResponse(BaseModel):
    """Score drift detection between consecutive snapshots."""
    current_score: float
    previous_score: float
    delta: float
    drift_detected: bool
    drift_severity: Optional[str] = None
    contributing_factors: List[str] = Field(default_factory=list)
