from fastapi import APIRouter, Depends, HTTPException, Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.auth import require_auth
from app.schemas.decision import ProjectReadinessRequest, ProjectReadinessResponse, RecommendedAction, DecisionAction
from app.api.v1.readiness import _placeholder_scoring_inputs
from app.services.decision_engine import project_readiness
from app.services.scoring import calculate_readiness_delta
from app.models.organization import Organization
from app.models.assessment import Assessment

router = APIRouter(prefix="/decisions", tags=["decisions"])

def _get_current_state(db: Session, org_id: str) -> Dict[str, Any]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    assessment = db.query(Assessment).filter(
        Assessment.organization_id == org_id, 
        Assessment.status != "archived"
    ).first()
    
    assessment_score = 0.0
    if assessment and assessment.overall_score is not None:
        assessment_score = float(assessment.overall_score)
        
    inputs = _placeholder_scoring_inputs(org_id)
    verified_controls = inputs["verified_controls"]
    verified_coverages = inputs["verified_coverages"]
    lifecycle_risks = inputs["lifecycle_risks"]
    exposure_risks = inputs["exposure_risks"]
        
    # Get actual baseline score
    actual = calculate_readiness_delta(
        assessment_score, verified_controls, verified_coverages, lifecycle_risks, exposure_risks
    )
    
    return {
        "assessment_score": assessment_score,
        "verified_controls": verified_controls,
        "verified_coverages": verified_coverages,
        "lifecycle_risks": lifecycle_risks,
        "exposure_risks": exposure_risks,
        "previous_readiness_score": actual["final_readiness"]
    }

@router.get("/recommended-actions/{org_id}", response_model=List[RecommendedAction])
def get_recommended_actions(
    org_id: str = Path(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Returns a prioritized list of recommended actions that would increase readiness score.
    """
    state = _get_current_state(db, org_id)
    recommendations = []
    
    # 1. Remediate Exposure Risks
    for risk in state["exposure_risks"]:
        software = risk.get("software_name")
        if software:
            action = DecisionAction(type="REMEDIATE_EXPOSURE", software_name=software)
            proj = project_readiness(
                state["assessment_score"], state["verified_controls"], state["verified_coverages"],
                state["lifecycle_risks"], state["exposure_risks"],
                [action.model_dump()], state["previous_readiness_score"]
            )
            delta = proj.get("readiness_delta", 0.0)
            if delta > 0:
                recommendations.append(RecommendedAction(
                    action=action,
                    projected_delta=delta,
                    description=f"Remediate exposure vulnerabilities in {software}"
                ))

    # 2. Remediate Lifecycle Risks
    for risk in state["lifecycle_risks"]:
        software = risk.get("software_name")
        if software:
            action = DecisionAction(type="REMEDIATE_LIFECYCLE", software_name=software)
            proj = project_readiness(
                state["assessment_score"], state["verified_controls"], state["verified_coverages"],
                state["lifecycle_risks"], state["exposure_risks"],
                [action.model_dump()], state["previous_readiness_score"]
            )
            delta = proj.get("readiness_delta", 0.0)
            if delta > 0:
                recommendations.append(RecommendedAction(
                    action=action,
                    projected_delta=delta,
                    description=f"Upgrade {software} to a supported version"
                ))
                
    # Sort by highest delta first
    recommendations.sort(key=lambda x: x.projected_delta, reverse=True)
    return recommendations

@router.post("/project/{org_id}", response_model=ProjectReadinessResponse)
def project_decisions(
    request: ProjectReadinessRequest,
    org_id: str = Path(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_auth)
):
    """
    Projects the readiness score given a set of hypothetical actions.
    """
    state = _get_current_state(db, org_id)
    
    actions = [a.model_dump() for a in request.actions]
    
    proj = project_readiness(
        state["assessment_score"], state["verified_controls"], state["verified_coverages"],
        state["lifecycle_risks"], state["exposure_risks"],
        actions, state["previous_readiness_score"]
    )
    
    return ProjectReadinessResponse(**proj)
