from fastapi import APIRouter
from app.services.clinic_engine.engine import ClinicEngine
from app.services.clinic_engine.morning_check import MorningCheckGenerator, MorningCheck

router = APIRouter(tags=["clinic"])

def get_legacy_findings():
    """Mock fetching raw telemetry/findings from legacy infrastructure."""
    return [
        {"id": "find-001", "rule_id": "inactive_user_active_token"},
        {"id": "find-002", "rule_id": "os_update_missing"},
        {"id": "find-003", "rule_id": "backup_job_failed"}
    ]

@router.get("/morning-summary", response_model=MorningCheck)
async def get_morning_summary():
    """Returns the Morning Check for the clinic owner."""
    engine = ClinicEngine()
    generator = MorningCheckGenerator(engine)
    
    # In reality, fetch actual findings from existing backend services here
    raw_findings = get_legacy_findings()
    
    check = generator.generate(raw_findings)
    return check

@router.post("/problems/{problem_id}/fix")
async def fix_problem(problem_id: str):
    """Triggers the autofix for a given problem."""
    # MVP mock to trigger remediation engine
    return {"status": "success", "message": f"Fix triggered for {problem_id}"}
