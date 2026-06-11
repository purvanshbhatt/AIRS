"""
Governance Policy Pydantic Schemas — CRUD, evaluation, and violation models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────

class PolicyCreateRequest(BaseModel):
    """Create a new governance policy."""
    name: str = Field(..., description="Policy name")
    description: Optional[str] = Field(None, description="Policy description")
    policy_type: str = Field(..., description="Policy type (ai_usage, model_approval, vendor_risk, deployment_gate, environment_restriction, data_handling)")
    policy_definition: Dict[str, Any] = Field(..., description="JSON policy definition with 'rules' array")
    enforcement_mode: str = Field("audit", description="Enforcement mode: enforce, audit, disabled")


class PolicyUpdateRequest(BaseModel):
    """Partial update of a governance policy."""
    name: Optional[str] = None
    description: Optional[str] = None
    policy_definition: Optional[Dict[str, Any]] = None
    enforcement_mode: Optional[str] = None
    is_active: Optional[bool] = None


# ── Response Schemas ─────────────────────────────────────────────────

class PolicyResponse(BaseModel):
    """Full governance policy representation."""
    id: str
    org_id: str
    name: str
    description: Optional[str] = None
    policy_type: str
    policy_definition: Dict[str, Any]
    version: int = 1
    is_active: bool = True
    enforcement_mode: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class PolicyViolationResponse(BaseModel):
    """A single policy rule violation."""
    rule_index: int
    condition: str
    requirement: str
    severity: str
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    details: Optional[str] = None
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None


class PolicyEvaluationResponse(BaseModel):
    """Result of evaluating a single policy."""
    policy_id: str
    policy_name: str
    result: str  # pass, fail, warn
    violations: List[PolicyViolationResponse]
    assets_evaluated: int
    enforcement_mode: str


class PolicyEvaluateAllResponse(BaseModel):
    """Results of evaluating all active policies."""
    results: List[PolicyEvaluationResponse]
    total_policies: int
    total_violations: int
    passing: int
    failing: int
    warning: int


class PolicyEvaluationLogResponse(BaseModel):
    """Historical evaluation log entry."""
    id: str
    policy_id: str
    org_id: str
    evaluation_context: Optional[Dict[str, Any]] = None
    result: str
    violations: Optional[List[Any]] = None
    evaluated_at: Optional[datetime] = None
    evaluated_by: Optional[str] = None

    model_config = {"from_attributes": True}
