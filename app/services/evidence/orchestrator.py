from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.schemas.evidence import NormalizedEvidence, EvidenceCollectionResult
from app.models.evidence import EvidenceLedger, NormalizedEvidenceRecord
import logging

logger = logging.getLogger("airs.evidence_orchestrator")

class EvidenceOrchestrator:
    """
    Manages the ingestion of NormalizedEvidence into the EvidenceRegistry and EvidenceLedger.
    """
    def __init__(self, db: Session):
        self.db = db
        
    def ingest_collection_result(self, org_id: str, connector_id: str, result: EvidenceCollectionResult) -> Dict[str, int]:
        """
        Takes a collection result from any adapter, saves it to the immutable ledger,
        and adds it to the normalized evidence queue for verification.
        """
        new_count = 0
        duplicate_count = 0
        
        for evidence in result.evidence:
            # Check if hash already exists in ledger
            existing = self.db.query(EvidenceLedger).filter_by(evidence_hash=evidence.evidence_hash).first()
            if existing:
                duplicate_count += 1
                continue
                
            # Create immutable ledger entry
            ledger_entry = EvidenceLedger(
                org_id=org_id,
                connector_id=connector_id,
                evidence_hash=evidence.evidence_hash,
                timestamp=evidence.timestamp,
                source_name=result.provider_name,
                event_type=evidence.event_type,
                raw_payload=evidence.raw_payload,
                confidence_freshness=evidence.confidence.freshness,
                confidence_completeness=evidence.confidence.completeness,
                confidence_integrity=evidence.confidence.integrity,
                confidence_availability=evidence.confidence.availability,
                overall_confidence=evidence.confidence.overall_confidence
            )
            self.db.add(ledger_entry)
            
            # Create normalized record for Verification Engine
            normalized_entry = NormalizedEvidenceRecord(
                org_id=org_id,
                evidence_hash=evidence.evidence_hash,
                asset_id=evidence.asset_id,
                control_id=evidence.control_id,
                severity=evidence.severity.value,
                processed=False
            )
            self.db.add(normalized_entry)
            new_count += 1
            
        self.db.commit()
        return {"new": new_count, "duplicates": duplicate_count}
