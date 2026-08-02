import copy
from typing import List, Dict, Any, Optional
from app.services.scoring import calculate_readiness_delta

def project_readiness(
    current_assessment_score: float,
    current_verified_controls: List[Dict[str, Any]],
    current_verified_coverages: List[Dict[str, Any]],
    current_lifecycle_risks: List[Dict[str, Any]],
    current_exposure_risks: List[Dict[str, Any]],
    proposed_actions: List[Dict[str, Any]],
    previous_readiness_score: Optional[float] = None
) -> Dict[str, Any]:
    """
    Project readiness score based on proposed actions using deterministic scoring.
    Delegates entirely to `app.services.scoring.calculate_readiness_delta`.
    """
    # Clone state
    assessment_score = current_assessment_score
    verified_controls = copy.deepcopy(current_verified_controls)
    verified_coverages = copy.deepcopy(current_verified_coverages)
    lifecycle_risks = copy.deepcopy(current_lifecycle_risks)
    exposure_risks = copy.deepcopy(current_exposure_risks)
    
    for action in proposed_actions:
        action_type = action.get("type")
        
        if action_type == "VERIFY_CONTROL":
            if "control" in action:
                verified_controls.append(action["control"])
                
        elif action_type == "IMPROVE_COVERAGE":
            if "coverage" in action:
                verified_coverages.append(action["coverage"])
                
        elif action_type == "REMEDIATE_LIFECYCLE":
            software_name = action.get("software_name")
            if software_name:
                lifecycle_risks = [risk for risk in lifecycle_risks if risk.get("software_name") != software_name]
                
        elif action_type == "REMEDIATE_EXPOSURE":
            software_name = action.get("software_name")
            if software_name:
                exposure_risks = [risk for risk in exposure_risks if risk.get("software_name") != software_name]
                
        elif action_type == "IMPROVE_ASSESSMENT":
            score_increase = action.get("score_increase", 0.0)
            assessment_score += float(score_increase)
            assessment_score = min(100.0, assessment_score)

    return calculate_readiness_delta(
        assessment_score=assessment_score,
        verified_controls=verified_controls,
        verified_coverages=verified_coverages,
        lifecycle_risks=lifecycle_risks,
        exposure_risks=exposure_risks,
        previous_readiness_score=previous_readiness_score
    )
