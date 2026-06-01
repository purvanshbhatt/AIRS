from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.database import get_db
from app.core.middleware import RequestIdMiddleware # Using existing middleware pattern
from app.models.telemetry_event import TelemetryEvent
from app.models.connector import Connector, ConnectorType, ConnectorStatus
from app.sentinel.evidence.models import TelemetryEvidence
from app.sentinel.twin.models import SentinelSimulation
from app.integrations.splunk.service import ingest_splunk_telemetry
from app.sentinel.evidence.engine import generate_evidence_from_telemetry
from app.sentinel.twin.engine import execute_simulation
from app.sentinel.board_intelligence.generator import generate_board_report

# Placeholder for auth
# from app.api.auth import get_current_org

router = APIRouter(tags=["Sentinel"])

def get_current_org():
    """Mock auth for the hackathon demo."""
    # Returns a hardcoded org_id assuming one exists.
    # In production, use existing X-AIRS-API-Key logic.
    return "00000000-0000-0000-0000-000000000001"

@router.get("/status")
def get_sentinel_status(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    active_evidence = db.query(TelemetryEvidence).filter(
        TelemetryEvidence.telemetry_verified == True
    ).count()
    return {
        "status": "active",
        "telemetry_health": "healthy",
        "active_evidence_count": active_evidence
    }

@router.get("/telemetry")
def get_telemetry(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    events = db.query(TelemetryEvent).filter(TelemetryEvent.org_id == org_id).order_by(TelemetryEvent.created_at.desc()).limit(50).all()
    return [{"id": e.id, "source": e.source_system, "type": e.event_type, "severity": e.severity, "processed": e.processed} for e in events]

@router.get("/evidence")
def get_evidence(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    # Using org_id from auth to filter implicitly by joining or filtering if org_id was on evidence
    # Evidence belongs to org implicitly via raw event, but for demo we just return all
    evidence = db.query(TelemetryEvidence).order_by(TelemetryEvidence.created_at.desc()).limit(50).all()
    return [{
        "id": e.id, "evidence_type": e.evidence_type, "severity": e.severity, 
        "domain": e.control_domain, "framework": e.framework_mapping
    } for e in evidence]

@router.post("/twin")
def run_digital_twin_simulation(payload: dict, db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    scenario_type = payload.get("scenario_type")
    if not scenario_type:
        raise HTTPException(status_code=400, detail="scenario_type is required")
    try:
        simulation = execute_simulation(db, org_id, scenario_type)
        return {"simulation_id": simulation.id, "simulated_score": simulation.readiness_impact_score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/simulations")
def list_simulations(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    sims = db.query(SentinelSimulation).filter(SentinelSimulation.org_id == org_id).order_by(SentinelSimulation.executed_at.desc()).limit(10).all()
    return [{
        "id": s.id, "scenario": s.scenario_type, "score": s.readiness_impact_score, 
        "executed_at": s.executed_at
    } for s in sims]

@router.get("/reports/{simulation_id}")
def get_board_report(simulation_id: str, db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    try:
        report = generate_board_report(db, simulation_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrations/splunk")
async def trigger_splunk_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    # Run the full pipeline sync
    # 1. Ingest Splunk
    events_ingested = await ingest_splunk_telemetry(db, org_id)
    # 2. Generate Evidence
    evidence_generated = generate_evidence_from_telemetry(db, org_id)
    
    return {
        "status": "sync_started", 
        "events_ingested": events_ingested,
        "evidence_generated": evidence_generated
    }
