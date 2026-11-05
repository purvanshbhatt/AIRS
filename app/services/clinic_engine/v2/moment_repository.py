import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.clinic_moment import ClinicMomentRecord, MomentStatus
from app.services.clinic_engine.v2.schema import ClinicMoment

logger = logging.getLogger(__name__)

class MomentRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def save_moments(self, org_id: str, moments: List[ClinicMoment]):
        """Persists generated moments into the backend repository."""
        for m in moments:
            existing = self.db.query(ClinicMomentRecord).filter(ClinicMomentRecord.id == m.id).first()
            if not existing:
                actions_dump = []
                for a in m.actions:
                    ad = a.model_dump()
                    ad["automation_type"] = a.automation_type
                    ad["automation_params"] = a.automation_params
                    actions_dump.append(ad)
                    
                record = ClinicMomentRecord(
                    id=m.id,
                    org_id=org_id,
                    question_id=m.question_id,
                    capability_id=m.capability_id,
                    verdict=m.verdict.value,
                    confidence=m.confidence,
                    severity=m.severity,
                    translation=m.translation.model_dump(),
                    actions=actions_dump,
                    evidence_ids=m.evidence_ids,
                    status=MomentStatus.ACTIVE,
                    generated_at=m.generated_at,
                    execution_history=[]
                )
                self.db.add(record)
            else:
                # Update expiration or keep it active
                existing.status = MomentStatus.ACTIVE
                
        self.db.commit()
        
    def get_moment(self, moment_id: str) -> Optional[ClinicMomentRecord]:
        return self.db.query(ClinicMomentRecord).filter(ClinicMomentRecord.id == moment_id).first()
        
    def add_audit_log(self, moment_id: str, actor: str, action: str, result: str, success: bool):
        record = self.get_moment(moment_id)
        if record:
            history = list(record.execution_history) if record.execution_history else []
            history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "action": action,
                "result": result,
                "success": success
            })
            
            # Reassign to trigger SQLAlchemy JSON mutation detection
            record.execution_history = history
            self.db.commit()
            
    def mark_resolved(self, moment_id: str, resolved_by: str, method: MomentStatus = MomentStatus.RESOLVED_MANUALLY):
        record = self.get_moment(moment_id)
        if record:
            record.status = method
            record.resolved_at = datetime.now(timezone.utc)
            record.resolved_by = resolved_by
            self.db.commit()
