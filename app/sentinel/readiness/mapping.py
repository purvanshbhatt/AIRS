"""
Readiness Impact Mapping.

Translates active TelemetryEvidence into overrides or inputs for the 
existing ResilAI scoring engine.
"""
import logging
from sqlalchemy.orm import Session
from app.sentinel.evidence.models import TelemetryEvidence
from app.sentinel.evidence.enums import EvidenceType

logger = logging.getLogger("airs.sentinel.readiness")

# Single Source of Truth mapping evidence to core rubric questions
EVIDENCE_TO_QUESTION_MAPPING = {
    EvidenceType.FAILED_BACKUP_VALIDATION: {"q_id": "rs_03", "override_answer": False, "status": "STALE_CONNECTION"},
    EvidenceType.MISSING_MFA: {"q_id": "iv_01", "override_answer": False, "status": "STALE_CONNECTION"},
    EvidenceType.INACTIVE_EDR: {"q_id": "dc_01", "override_answer": "Unknown / Not Measured", "status": "STALE_CONNECTION"},
    EvidenceType.LOGGING_GAP: {"q_id": "tl_02", "override_answer": False, "status": "STALE_CONNECTION"},
    EvidenceType.OVERDUE_DR_TESTING: {"q_id": "rs_05", "override_answer": "Undefined / No Target", "status": "STALE_CONNECTION"},
    EvidenceType.CRITICAL_VULNERABILITY: {"q_id": "dc_06", "override_answer": False, "status": "STALE_CONNECTION"},
    EvidenceType.CLOUD_MISCONFIGURATION: {"q_id": "iv_04", "override_answer": False, "status": "STALE_CONNECTION"},
    EvidenceType.RANSOMWARE_INDICATOR: {"q_id": "dc_06", "override_answer": False, "status": "STALE_CONNECTION"},
    EvidenceType.DATA_EXFILTRATION_INDICATOR: {"q_id": "dc_02", "override_answer": False, "status": "STALE_CONNECTION"},
    EvidenceType.AI_AGENT_ABUSE_INDICATOR: {"q_id": "iv_06", "override_answer": False, "status": "STALE_CONNECTION"}
}

def generate_readiness_inputs(db: Session, org_id: str) -> dict:
    """
    Fetches active TelemetryEvidence and maps it to verification_statuses
    and potential answer overrides for the scoring engine.
    
    Returns a dict with 'answers_override' and 'verification_override'.
    """
    active_evidence = db.query(TelemetryEvidence).filter(
        TelemetryEvidence.telemetry_verified == True
    ).all()
    
    verification_override = {}
    answers_override = {}
    
    for evidence in active_evidence:
        mapping = EVIDENCE_TO_QUESTION_MAPPING.get(evidence.evidence_type)
        if mapping:
            q_id = mapping["q_id"]
            verification_override[q_id] = mapping["status"]
            answers_override[q_id] = mapping["override_answer"]
            
    return {
        "answers_override": answers_override,
        "verification_override": verification_override
    }
