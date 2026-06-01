"""
Telemetry Evidence Engine for ResilAI Sentinel.
Converts raw TelemetryEvents into deterministic TelemetryEvidence.
"""
import uuid
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.telemetry_event import TelemetryEvent
from .models import TelemetryEvidence
from app.core.rubric import get_question, get_domain_nist_function
from app.sentinel.readiness.mapping import EVIDENCE_TO_QUESTION_MAPPING
from app.sentinel.evidence.enums import EvidenceType

logger = logging.getLogger("airs.sentinel.evidence")

# Deterministic Rules mapping evidence_type to severity/confidence (framework mapping is dynamic)
EVIDENCE_RULES = {
    EvidenceType.FAILED_BACKUP_VALIDATION: {"severity": "high", "confidence": 1.0},
    EvidenceType.MISSING_MFA: {"severity": "high", "confidence": 1.0},
    EvidenceType.INACTIVE_EDR: {"severity": "critical", "confidence": 1.0},
    EvidenceType.LOGGING_GAP: {"severity": "medium", "confidence": 0.8},
    EvidenceType.OVERDUE_DR_TESTING: {"severity": "high", "confidence": 1.0},
    EvidenceType.CRITICAL_VULNERABILITY: {"severity": "critical", "confidence": 0.9},
    EvidenceType.CLOUD_MISCONFIGURATION: {"severity": "medium", "confidence": 0.9},
    EvidenceType.RANSOMWARE_INDICATOR: {"severity": "critical", "confidence": 1.0},
    EvidenceType.DATA_EXFILTRATION_INDICATOR: {"severity": "critical", "confidence": 1.0},
    EvidenceType.AI_AGENT_ABUSE_INDICATOR: {"severity": "high", "confidence": 0.8}
}

def generate_evidence_from_telemetry(db: Session, org_id: str) -> int:
    """
    Processes unprocessed TelemetryEvents for an org and converts them 
    into deterministic TelemetryEvidence records.
    """
    unprocessed_events = db.query(TelemetryEvent).filter(
        TelemetryEvent.org_id == org_id,
        TelemetryEvent.processed == False
    ).all()
    
    evidence_created = 0
    
    for event in unprocessed_events:
        try:
            try:
                evidence_type = EvidenceType(event.event_type)
            except ValueError:
                logger.debug(f"Invalid evidence type: {event.event_type}")
                event.processed = True
                event.processed_at = datetime.now(timezone.utc)
                continue
            
            rule = EVIDENCE_RULES.get(evidence_type)
            mapping = EVIDENCE_TO_QUESTION_MAPPING.get(evidence_type)
            
            if not rule or not mapping:
                logger.debug(f"No evidence rule or mapping found for event type: {evidence_type}")
                event.processed = True
                event.processed_at = datetime.now(timezone.utc)
                continue
                
            payload = event.payload or {}
            title = payload.get("title", f"Telemetry Detection: {evidence_type.replace('_', ' ').title()}")
            description = payload.get("description", payload.get("raw", ""))
            
            # Dynamic Framework Resolution
            q_id = mapping["q_id"]
            question_data, domain_id = get_question(q_id)
            
            control_domain = None
            framework_mapping = None
            
            if domain_id:
                nist_func = get_domain_nist_function(domain_id)
                control_domain = domain_id
                if nist_func and "name" in nist_func:
                    framework_mapping = f"NIST CSF {nist_func['name']}"
            
            evidence = TelemetryEvidence(
                id=str(uuid.uuid4()),
                source=event.source_system,
                source_reference=event.source_event_id,
                event_type=event.event_type,
                evidence_type=evidence_type,
                severity=rule["severity"],
                title=title,
                description=description,
                timestamp=event.created_at,
                confidence=rule["confidence"],
                telemetry_verified=True,
                control_domain=control_domain,
                framework_mapping=framework_mapping,
                raw_event_reference=event.id
            )
            
            db.add(evidence)
            evidence_created += 1
            
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Failed to generate evidence for event {event.id}: {e}")
            
    if evidence_created > 0:
        db.commit()
        logger.info(f"Generated {evidence_created} new TelemetryEvidence records for org {org_id}")
        
    return evidence_created
