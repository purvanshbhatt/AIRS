from typing import List, Any
from app.services.clinic_engine.models import ClinicMoment
from app.services.clinic_engine.registry import ClinicMomentRegistry

class ClinicEngine:
    def process_findings(self, raw_findings: List[Any]) -> List[ClinicMoment]:
        """
        Takes raw enterprise findings and converts them into Clinic Moments.
        Determines business priority.
        """
        moments = []
        for finding in raw_findings:
            moment = ClinicMomentRegistry.evaluate_finding(finding)
            if moment:
                moments.append(moment)
        
        # Sort by severity (high first) then by estimated fix time
        def sort_key(m: ClinicMoment):
            severity_weight = 0 if m.severity == "high" else 1 if m.severity == "medium" else 2
            return (severity_weight, m.estimated_fix_time_mins)
            
        moments.sort(key=sort_key)
        return moments
