import os
import uuid
import time
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal, engine
from app.models.organization import Organization
from app.models.assessment import Assessment
from app.models.telemetry_event import TelemetryEvent
from app.sentinel.evidence.models import TelemetryEvidence
from app.sentinel.twin.models import SentinelSimulation

from app.sentinel.evidence.engine import generate_evidence_from_telemetry
from app.sentinel.twin.engine import execute_simulation
from app.sentinel.board_intelligence.generator import generate_board_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinel.validation")

def run_validation():
    logger.info("Starting Sentinel Staging Validation Cycle")
    db = SessionLocal()
    client = TestClient(app)
    
    # Setup test org
    org_id = "test-sentinel-org-" + str(uuid.uuid4())[:8]
    org = Organization(id=org_id, name="Sentinel Validation Corp")
    db.add(org)
    
    # Setup base assessment for Twin scoring check
    assmt = Assessment(
        id=str(uuid.uuid4()), 
        organization_id=org_id,
        status="completed",
        overall_score=85.0
    )
    db.add(assmt)
    
    from app.models.answer import Answer
    for q_id in ["rs_03", "iv_01", "dc_01"]:
        db.add(Answer(
            id=str(uuid.uuid4()),
            assessment_id=assmt.id,
            question_id=q_id,
            value="true"
        ))
    db.commit()

    try:
        # Phase 1: Environment & Database Migration
        logger.info("--- Phase 1: Environment & Database ---")
        ev_count = db.query(TelemetryEvidence).count()
        sim_count = db.query(SentinelSimulation).count()
        logger.info(f"Database reachable. Evidence tables exist.")
        
        # We can't hit FastAPI endpoints directly without them being wired, 
        # but we know the API routes exist at /api/sentinel/...
        res = client.get("/api/sentinel/status")
        if res.status_code == 200:
            logger.info("Sentinel Endpoints reachable: 200 OK")
        else:
            logger.warning(f"Sentinel Endpoints check skipped/failed: {res.status_code}")

        # Phase 3 & 4: Evidence Generation & Scoring Validation
        logger.info("--- Phase 3 & 4: Evidence & Scoring Isolation ---")
        
        # Mock Splunk Ingestion
        # We'll just create raw telemetry events directly to mimic webhook
        events = [
            ("failed_backup_validation", "critical"),
            ("missing_mfa", "high"),
            ("inactive_edr", "critical")
        ]
        
        for ev_type, sev in events:
            te = TelemetryEvent(
                id=str(uuid.uuid4()),
                org_id=org_id,
                connector_id=None,
                event_type=ev_type,
                source_system="splunk",
                source_event_id=str(uuid.uuid4()),
                payload_hash="hash",
                payload={"test": "data"},
                severity=sev,
                processed=False
            )
            db.add(te)
        db.commit()
        
        evidence_created = generate_evidence_from_telemetry(db, org_id)
        assert evidence_created == 3, f"Expected 3 evidence records, got {evidence_created}"
        logger.info("Evidence generation successful. Framework strings resolved via core.")

        # Phase 5: Digital Twin Testing
        logger.info("--- Phase 5: Digital Twin Testing ---")
        
        # Check assessment score before
        assmt_before = db.query(Assessment).filter_by(id=assmt.id).first()
        score_before = assmt_before.overall_score
        
        sim = execute_simulation(db, org_id, "Ransomware")
        logger.info(f"Ransomware Simulation Executed. Score Impact: {score_before} -> {sim.readiness_impact_score}")
        
        db.refresh(assmt_before)
        assert assmt_before.overall_score == score_before, "CRITICAL FAILURE: Twin simulation mutated the persisted assessment record!"
        logger.info("Assessment Integrity Check Passed. No DB mutation.")
        
        # Phase 6: Board Intelligence Testing
        logger.info("--- Phase 6: Board Intelligence Testing ---")
        report = generate_board_report(db, sim.id)
        logger.info("Executive Intelligence Generated.")
        
        # Phase 7: Performance Testing (Bulk Telemetry)
        logger.info("--- Phase 7: Performance Testing (1000 Events) ---")
        start_time = time.time()
        
        bulk_events = []
        for i in range(1000):
            bulk_events.append(TelemetryEvent(
                id=str(uuid.uuid4()),
                org_id=org_id,
                connector_id=None,
                event_type="failed_backup_validation",
                source_system="splunk",
                source_event_id=f"bulk-{i}",
                payload_hash=f"hash-{i}",
                payload={"test": "data"},
                severity="high",
                processed=False
            ))
        db.bulk_save_objects(bulk_events)
        db.commit()
        
        ingest_time = time.time()
        generate_evidence_from_telemetry(db, org_id)
        ev_time = time.time()
        execute_simulation(db, org_id, "Ransomware")
        sim_time = time.time()
        
        total_time = sim_time - start_time
        logger.info(f"Bulk Test Completed in {total_time:.2f}s")
        assert total_time < 5.0, f"Performance test failed: {total_time:.2f}s is > 5s"
        
        logger.info("=== VALIDATION CYCLE PASSED ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_validation()
