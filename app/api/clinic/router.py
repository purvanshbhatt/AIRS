from fastapi import APIRouter
from typing import List
import time
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter
from app.services.clinic_engine.v2.schema import RawEvent
from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
from app.services.clinic_engine.v2.morning_check import MorningCheckGeneratorV2, MorningCheckV2
from app.services.clinic_engine.v2.providers import ProviderRegistry

router = APIRouter(tags=["clinic"])

def get_demo_telemetry() -> List[RawEvent]:
    """
    Simulates fetching LIVE telemetry from connected systems for DEMO organizations.
    In production, this telemetry is fetched asynchronously by connector sync jobs.
    """
    now = datetime.now(timezone.utc)
    
    # 1. Microsoft Graph Telemetry (Entra ID, Intune, Defender)
    ms_event = RawEvent(
        event_type="microsoft.telemetry",
        source_system="microsoft",
        source_event_id=f"sync-ms-{int(time.time())}",
        organization_id="default-org",
        payload={
            "entra_users": [
                {
                    "user_id": "u-001",
                    "user_principal_name": "dr.smith@clinic.com",
                    "mfa_enforced": True,
                    "account_enabled": True,
                    "last_sign_in": (now - timedelta(hours=2)).isoformat(),
                    "conditional_access_status": "enforced"
                },
                {
                    "user_id": "u-002",
                    "user_principal_name": "former.nurse@clinic.com",
                    "mfa_enforced": False,
                    "account_enabled": True,
                    "last_sign_in": (now - timedelta(days=45)).isoformat(),  # Stale! (Q1)
                    "conditional_access_status": "unknown"
                }
            ],
            "intune_devices": [
                {
                    "device_id": "d-001",
                    "device_name": "FRONT-DESK-PC",
                    "compliance_state": "noncompliant", # Non-compliant! (Q3)
                    "bitlocker_status": "not_encrypted",
                    "os_version": "10.0.19044"
                }
            ],
            "defender_alerts": [
                {
                    "alert_id": "a-001",
                    "title": "Suspicious PowerShell execution",
                    "severity": "high",
                    "status": "active",
                    "device_id": "d-001"
                }
            ]
        }
    )

    # 2. Veeam Backup Telemetry (Assuming a backup connector returns this)
    backup_event = RawEvent(
        event_type="veeam.backup_job",
        source_system="veeam",
        source_event_id=f"sync-v-{int(time.time())}",
        organization_id="default-org",
        payload={
            "system_name": "Patient Database Server",
            "last_successful_backup": (now - timedelta(hours=28)).isoformat(), # Failed! (Q2)
            "backup_type": "full"
        }
    )
    
    return [ms_event, backup_event]


from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.clinic_engine.v2.moment_repository import MomentRepository

@router.get("/morning-summary", response_model=MorningCheckV2)
async def get_morning_summary(db: Session = Depends(get_db)):
    """Returns the Morning Safety Check for the clinic owner."""
    
    # 1. For Morning Check V2 (Internal Demo logic)
    events = get_demo_telemetry()
    
    # 2. Extract Evidence from Telemetry using Providers
    evidence = []
    for provider_cls in ProviderRegistry.list_all().values():
        evidence.extend(provider_cls.extract(events))
        
    # 3. Evaluate Evidence against Capabilities
    engine = ClinicEvaluationEngine()
    moments = engine.evaluate(evidence)
    
    # 4. Save to Repository
    repo = MomentRepository(db)
    # Using a dummy org_id for now as there's no auth context
    repo.save_moments(org_id="default-org", moments=moments)
    
    # 5. Generate the final Morning Check
    generator = MorningCheckGeneratorV2()
    check = generator.generate(moments)
    
    return check

from app.services.clinic_engine.v2.contracts import DailyReadinessReport
from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine
from app.services.clinic_engine.v2.pilot import PilotService
from app.services.clinic_engine.v2.metrics_engine import MetricsEngine

@router.get("/readiness/{org_id}", response_model=DailyReadinessReport)
async def get_clinic_readiness(org_id: str, db: Session = Depends(get_db)):
    """The product endpoint. Returns the immutable DailyReadinessReport."""
    # 1. Pilot Service: Seed demo clinic if it doesn't exist
    pilot = PilotService(db)
    if pilot.get_mode(org_id) == "demo" or not pilot.get_mode(org_id):
        pilot.seed_demo_clinic(org_id)
        
    # 2. Fetch raw telemetry
    # In a real system, evidence is generated asynchronously by connectors.
    # For MVP validation, we load demo telemetry if in demo mode.
    if pilot.get_mode(org_id) == "demo" or not pilot.get_mode(org_id):
        events = get_demo_telemetry()
    else:
        events = [] # Replace with real DB fetch of recent RawEvents in production
    
    # 3. Extract Evidence
    evidence = []
    for provider_cls in ProviderRegistry.list_all().values():
        evidence.extend(provider_cls.extract(events))
        
    # 4. Evaluate Capabilities -> Moments
    engine = ClinicEvaluationEngine()
    moments = engine.evaluate(evidence)
    
    # 5. Build Readiness Report (The Product Layer)
    readiness_engine = ReadinessEngine(db)
    report = readiness_engine.evaluate(org_id, moments)
    
    # 6. Record Business Value Metrics
    metrics_engine = MetricsEngine(db)
    metrics_engine.record_daily_metrics(org_id, report)
    report.value = metrics_engine.get_summary(org_id, days=30)
    
    return report

from fastapi import HTTPException
from pydantic import BaseModel
from app.models.clinic_moment import MomentStatus

class OnboardRequest(BaseModel):
    clinic_name: str
    emr: str
    workspace: str

@router.post("/onboard")
async def onboard_clinic(req: OnboardRequest, db: Session = Depends(get_db)):
    """Initializes the clinic."""
    pilot = PilotService(db)
    # Using 'default-org' to align with the demo UI
    pilot.seed_demo_clinic("default-org")
    return {"status": "success", "org_id": "default-org"}

@router.post("/problems/{problem_id}/fix")
async def fix_problem(problem_id: str, db: Session = Depends(get_db)):
    """Triggers the autofix for a given problem."""
    repo = MomentRepository(db)
    record = repo.get_moment(problem_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Moment not found.")
        
    if record.status != MomentStatus.ACTIVE:
        return {"status": "error", "message": "This issue has already been resolved."}
        
    # Validation: re-evaluate live telemetry to see if the issue is still active
    # For MVP validation, we use demo telemetry
    events = get_demo_telemetry()
    evidence = []
    for provider_cls in ProviderRegistry.list_all().values():
        evidence.extend(provider_cls.extract(events))
        
    engine = ClinicEvaluationEngine()
    current_moments = engine.evaluate(evidence)
    
    is_still_valid = any(m.id == problem_id for m in current_moments)
    if not is_still_valid:
        # It's fixed, mark it
        repo.mark_resolved(problem_id, resolved_by="system", method=MomentStatus.RESOLVED_AUTOMATICALLY)
        return {"status": "error", "message": "This issue has already been resolved."}
        
    # Execute remediation (mock)
    # The actions are in `record.actions` which is a list of dicts.
    # We would use `automation_type` and `automation_params`.
    executed_action = None
    for action in record.actions:
        if action.get("can_automate"):
            executed_action = action
            break
            
    if not executed_action:
        raise HTTPException(status_code=400, detail="This issue cannot be automated.")
        
    # In a real system, we'd dispatch to a remediation worker using `executed_action["automation_params"]`
    
    repo.mark_resolved(problem_id, resolved_by="user_id", method=MomentStatus.RESOLVED_MANUALLY)
    repo.add_audit_log(
        moment_id=problem_id,
        actor="user_id",
        action=f"Execute {executed_action.get('automation_type')}",
        result="Success",
        success=True
    )
    
    return {"status": "success", "message": f"Fix triggered for {problem_id}"}
