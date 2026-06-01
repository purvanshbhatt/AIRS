"""
Digital Twin Simulation Engine.
Runs deterministic incident outcome simulations based on readiness posture.
"""
import copy
import logging
from sqlalchemy.orm import Session
from app.sentinel.twin.models import SentinelSimulation
from app.sentinel.evidence.models import TelemetryEvidence
from app.models.assessment import Assessment
from app.services.scoring import calculate_scores, get_recommendations
from app.sentinel.readiness.mapping import EVIDENCE_TO_QUESTION_MAPPING
from app.sentinel.evidence.enums import EvidenceType

logger = logging.getLogger("airs.sentinel.twin")

# Deterministic Simulation Scenarios (Removed base_impact_penalty as core rubric calculates this)
SCENARIOS = {
    "Ransomware": {
        "critical_controls": [EvidenceType.FAILED_BACKUP_VALIDATION, EvidenceType.INACTIVE_EDR, EvidenceType.MISSING_MFA]
    },
    "Data Exfiltration": {
        "critical_controls": [EvidenceType.MISSING_MFA, EvidenceType.LOGGING_GAP, EvidenceType.CLOUD_MISCONFIGURATION]
    },
    "Insider Threat": {
        "critical_controls": [EvidenceType.MISSING_MFA, EvidenceType.LOGGING_GAP]
    },
    "AI Agent Abuse": {
        "critical_controls": [EvidenceType.AI_AGENT_ABUSE_INDICATOR, EvidenceType.LOGGING_GAP]
    }
}

def execute_simulation(db: Session, org_id: str, scenario_type: str) -> SentinelSimulation:
    """
    Executes a deterministic simulation for the given scenario by piping overrides 
    into the core ResilAI scoring engine.
    """
    if scenario_type not in SCENARIOS:
        raise ValueError(f"Unknown scenario type: {scenario_type}")
        
    scenario = SCENARIOS[scenario_type]
    
    # 1. Fetch current active evidence
    active_evidence = db.query(TelemetryEvidence).filter(
        TelemetryEvidence.telemetry_verified == True
    ).all()
    
    active_types = []
    for e in active_evidence:
        try:
            active_types.append(EvidenceType(e.evidence_type))
        except ValueError:
            pass
    
    # 2. Get baseline readiness answers 
    latest_assessment = db.query(Assessment).filter(
        Assessment.organization_id == org_id,
        Assessment.status == "completed"
    ).order_by(Assessment.created_at.desc()).first()
    
    # Start with base answers, or empty if none exist
    if latest_assessment and latest_assessment.answers:
        base_answers = {a.question_id: a.get_typed_value() for a in latest_assessment.answers}
    else:
        base_answers = {}
    base_verifications = {} # Assuming standard verification if not provided
    
    # Calculate base score for context
    base_results = calculate_scores(base_answers, base_verifications)
    base_score = base_results.get("overall_score", 100.0)
        
    # 3. Apply Deterministic Overrides to Simulation State
    simulated_answers = copy.deepcopy(base_answers)
    simulated_verifications = copy.deepcopy(base_verifications)
    
    matched_weaknesses = []
    
    for critical_control in scenario["critical_controls"]:
        if critical_control in active_types:
            matched_weaknesses.append(critical_control.value)
            mapping = EVIDENCE_TO_QUESTION_MAPPING.get(critical_control)
            if mapping:
                q_id = mapping["q_id"]
                simulated_answers[q_id] = mapping["override_answer"]
                simulated_verifications[q_id] = mapping["status"]
            
    # 4. Calculate simulated post-incident score using the Core Rubric
    simulated_results = calculate_scores(simulated_answers, simulated_verifications)
    simulated_score = simulated_results.get("overall_score", 0.0)
    
    # 5. Get core recommendation gaps for the twin missing controls
    simulated_recommendations = get_recommendations(simulated_results)
    
    simulation = SentinelSimulation(
        org_id=org_id,
        scenario_type=scenario_type,
        status="completed",
        readiness_impact_score=simulated_score,
        weaknesses=matched_weaknesses,
        missing_controls=simulated_recommendations,
        simulation_context={
            "base_score": base_score,
            "scenario_details": scenario
        }
    )
    
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    
    logger.info(f"Executed {scenario_type} simulation for org {org_id}. Score: {base_score} -> {simulated_score}")
    
    return simulation
