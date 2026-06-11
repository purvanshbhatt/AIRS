from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.sentinel.db.database import get_sentinel_db
from app.integrations.sentinel_splunk.service import fetch_recent_security_events
from app.sentinel.twin.engine import recalculate_incident_readiness_score
from app.sentinel.board_intelligence.generator import generate_board_report_from_evidence

router = APIRouter()

class SimulationTriggerRequest(BaseModel):
    scenario: str = "Ransomware"
    org_id: str = "test-live-splunk-org"

@router.post("/trigger-simulation")
async def trigger_simulation(payload: SimulationTriggerRequest, db: Session = Depends(get_sentinel_db)):
    """
    Forces the Sentinel Agent to immediately query Splunk, fetch newly injected logs,
    run deterministic score recalculation, and generate the Gemini Board Report.
    """
    try:
        # 1. Fetch newly injected logs from Splunk, with Demo Fallback
        evidence_found = []
        try:
            evidence_found = await fetch_recent_security_events(minutes_back=15)
        except Exception as e:
            print(f"Splunk fetch failed or timed out: {e}. Utilizing fallback demo telemetry.")
            
        if not evidence_found:
            evidence_found = [{
                "timestamp": "2026-06-10T14:00:00Z",
                "host": "DEMO-HOST-01",
                "raw": 'EventCode=5379 User="hackathon_admin" Action="MFA Disabled" Status="Success"',
                "extracted_fields": {
                    "event_type": "mfa_disabled",
                    "severity": "high"
                }
            }]
        
        # 2. Run deterministic recalculation based on evidence severity
        scores = recalculate_incident_readiness_score(evidence_found)
        previous_score = scores["previous_score"]
        new_score = scores["new_score"]
        
        # 3. Generate the Gemini Board Report
        report = generate_board_report_from_evidence(previous_score, new_score, evidence_found)
        
        # 4. Return composite JSON
        return {
            "previous_score": previous_score,
            "new_score": new_score,
            "evidence_found": evidence_found,
            "executive_report": report
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
