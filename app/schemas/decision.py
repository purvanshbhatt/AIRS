from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DecisionAction(BaseModel):
    type: str = Field(..., description="Action type, e.g., VERIFY_CONTROL, IMPROVE_COVERAGE, REMEDIATE_LIFECYCLE, REMEDIATE_EXPOSURE")
    control: Optional[Dict[str, Any]] = None
    coverage: Optional[Dict[str, Any]] = None
    software_name: Optional[str] = None
    score_increase: Optional[float] = None

class ProjectReadinessRequest(BaseModel):
    actions: List[DecisionAction] = Field(..., max_length=50, description="Max 50 actions per projection")

class ProjectReadinessResponse(BaseModel):
    assessment_score: float
    modifiers: Dict[str, Any]
    final_readiness: float
    previous_readiness: Optional[float]
    readiness_delta: Optional[float]
    reasons: List[Dict[str, Any]]

class RecommendedAction(BaseModel):
    action: DecisionAction
    projected_delta: float
    description: str
