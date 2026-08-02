import hashlib
from typing import List, Dict
from datetime import datetime, timezone
from app.services.clinic_engine.v2.schema import Evidence, EvidenceKind, ClinicMoment, Verdict
from app.services.clinic_engine.v2.capability import CapabilityRegistry
import app.services.clinic_engine.v2.capabilities  # trigger auto-registration

class ClinicEvaluationEngine:
    def evaluate(self, evidence: List[Evidence]) -> List[ClinicMoment]:
        if not evidence:
            return []
            
        evidence_by_kind: Dict[EvidenceKind, List[Evidence]] = {}
        for e in evidence:
            evidence_by_kind.setdefault(e.kind, []).append(e)
            
        moments: List[ClinicMoment] = []
        
        for capability_cls in CapabilityRegistry.all_capabilities():
            cap_evidence = []
            for kind in capability_cls.required_evidence():
                cap_evidence.extend(evidence_by_kind.get(kind, []))
                
            results = capability_cls.evaluate(cap_evidence)
            for result in results:
                if result.verdict == Verdict.SAFE:
                    continue
                if result.confidence < capability_cls.confidence_threshold():
                    continue
                    
                sorted_evidence = sorted(result.evidence_used)
                hash_input = capability_cls.capability_id() + "".join(sorted_evidence)
                moment_id = hashlib.sha256(hash_input.encode()).hexdigest()
                
                severity = "high" if result.verdict == Verdict.CRITICAL else "medium"
                
                moment = ClinicMoment(
                    id=moment_id,
                    question_id=capability_cls.question_id(),
                    capability_id=capability_cls.capability_id(),
                    verdict=result.verdict,
                    confidence=result.confidence,
                    translation=capability_cls.translate(result),
                    actions=capability_cls.get_actions(result),
                    evidence_ids=result.evidence_used,
                    severity=severity,
                    generated_at=datetime.now(timezone.utc)
                )
                moments.append(moment)
                
        def sort_key(m: ClinicMoment):
            return 0 if m.verdict == Verdict.CRITICAL else 1
            
        moments.sort(key=sort_key)
        return moments
