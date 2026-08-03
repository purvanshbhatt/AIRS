import asyncio
import sys
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.organization import Organization
from app.services.clinic_engine.v2.contracts import DailyReadinessReport
from app.services.clinic_engine.v2.schema import RawEvent
from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
from app.services.clinic_engine.v2.providers import ProviderRegistry
from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine
from app.services.clinic_engine.v2.metrics_engine import MetricsEngine
from app.services.clinic_engine.v2.pilot import PilotService
from app.models.connector import Connector

def run_evaluation(org_id: str, events: List[RawEvent], db: Session) -> DailyReadinessReport:
    """Runs the full engine pipeline given an org and raw telemetry events."""
    evidence = []
    for provider_cls in ProviderRegistry.list_all().values():
        evidence.extend(provider_cls.extract(events))
        
    engine = ClinicEvaluationEngine()
    moments = engine.evaluate(evidence)
    
    readiness_engine = ReadinessEngine(db)
    report = readiness_engine.evaluate(org_id, moments)
    
    metrics_engine = MetricsEngine(db)
    metrics_engine.record_daily_metrics(org_id, report)
    report.value = metrics_engine.get_summary(org_id, days=30)
    
    return report

def generate_telemetry(scenario: str) -> List[RawEvent]:
    """Generates deterministic raw telemetry for a given scenario."""
    now = datetime.now(timezone.utc)
    
    ms_payload = {
        "entra_users": [
            {
                "user_id": "u-001",
                "user_principal_name": "dr.smith@sunshinedental.com",
                "mfa_enforced": True,
                "account_enabled": True,
                "last_sign_in": (now - timedelta(hours=2)).isoformat(),
                "conditional_access_status": "enforced"
            }
        ],
        "intune_devices": [
            {
                "device_id": "d-001",
                "device_name": "FRONT-DESK-PC",
                "compliance_state": "compliant",
                "bitlocker_status": "encrypted",
                "os_version": "10.0.19044"
            }
        ],
        "defender_alerts": []
    }
    
    veeam_payload = {
        "system_name": "Dentrix",
        "last_successful_backup": (now - timedelta(hours=2)).isoformat(),
        "backup_type": "full"
    }
    
    if scenario == "former_employee" or scenario == "multiple_issues":
        ms_payload["entra_users"].append({
            "user_id": "u-002",
            "user_principal_name": "former.nurse@sunshinedental.com",
            "mfa_enforced": False,
            "account_enabled": True,
            "last_sign_in": (now - timedelta(days=45)).isoformat(),
            "conditional_access_status": "unknown"
        })
        
    if scenario == "failed_backup" or scenario == "multiple_issues":
        veeam_payload["last_successful_backup"] = (now - timedelta(hours=28)).isoformat()
        
    if scenario == "critical_workstation" or scenario == "multiple_issues":
        ms_payload["intune_devices"][0]["compliance_state"] = "noncompliant"
        ms_payload["defender_alerts"].append({
            "alert_id": "a-001",
            "title": "Suspicious PowerShell execution",
            "severity": "high",
            "status": "active",
            "device_id": "d-001"
        })

    ms_event = RawEvent(
        event_type="microsoft.telemetry",
        source_system="microsoft",
        source_event_id=f"sync-ms-{int(time.time())}",
        organization_id="default-org",
        payload=ms_payload
    )
    
    veeam_event = RawEvent(
        event_type="veeam.backup_job",
        source_system="veeam",
        source_event_id=f"sync-v-{int(time.time())}",
        organization_id="default-org",
        payload=veeam_payload
    )
    
    if scenario == "no_telemetry":
        return []
    elif scenario == "connector_offline":
        # We will manually break the connector in DB, telemetry can still be empty
        return []
    elif scenario == "partial_visibility":
        return [ms_event]
        
    return [ms_event, veeam_event]

def setup_org(db: Session) -> str:
    org_id = str(uuid.uuid4())
    org = Organization(id=org_id, name="Test Clinic", owner_uid="test_user", org_mode="production")
    db.add(org)
    db.commit()
    
    pilot = PilotService(db)
    pilot.seed_demo_clinic(org_id)
    return org_id

def break_connectors(db: Session, org_id: str):
    connectors = db.query(Connector).filter(Connector.org_id == org_id).all()
    for c in connectors:
        c.health_status = "unreachable"
        c.last_sync_at = datetime.now(timezone.utc) - timedelta(days=2)
    db.commit()

def run_tests():
    db = SessionLocal()
    scenarios = [
        "perfect_clinic",
        "former_employee",
        "failed_backup",
        "critical_workstation",
        "multiple_issues",
        "connector_offline",
        "partial_visibility",
        "no_telemetry",
        "wazuh_offline"
    ]
    
    results = {}
    
    try:
        for scenario in scenarios:
            print(f"\\n--- Running Scenario: {scenario} ---")
            
            # Setup fresh org
            org_id = setup_org(db)
            
            if scenario in ["connector_offline", "no_telemetry"]:
                break_connectors(db, org_id)
            elif scenario == "partial_visibility":
                # Remove Veeam connector to simulate partial visibility
                db.query(Connector).filter(Connector.org_id == org_id, Connector.connector_type == "veeam").delete()
                db.commit()
            elif scenario == "wazuh_offline":
                w = db.query(Connector).filter(Connector.org_id == org_id, Connector.connector_type == "wazuh").first()
                if w:
                    w.health_status = "unreachable"
                    w.last_sync_at = datetime.now(timezone.utc) - timedelta(days=2)
                db.commit()
                
            events = generate_telemetry(scenario)
            
            start_time = time.time()
            report = run_evaluation(org_id, events, db)
            end_time = time.time()
            
            elapsed = end_time - start_time
            
            # Asserts & Checks
            status = report.status
            confidence = report.trust.confidence_pct
            
            print(f"Status: {status.value}")
            print(f"Confidence: {confidence}%")
            print(f"Failed Checks: {len(report.failed_checks)}")
            print(f"Unknowns: {len(report.unknowns)}")
            print(f"Warnings: {len(report.warnings)}")
            print(f"Time Taken: {elapsed:.3f}s")
            
            if scenario == "perfect_clinic":
                assert status == "safe_to_open"
                assert confidence >= 90
            elif scenario == "former_employee":
                # A former employee could be action_needed or critical depending on EMR access
                # In pilot.py, Jane Doe is terminated but has EMR access -> critical risk
                assert status == "critical_risk"
            elif scenario == "failed_backup":
                assert status == "critical_risk"
            elif scenario == "critical_workstation":
                assert status == "critical_risk"
            elif scenario == "multiple_issues":
                assert status == "critical_risk"
                assert len(report.failed_checks) >= 2
            elif scenario == "connector_offline":
                assert status != "safe_to_open"
                assert confidence < 70
            elif scenario == "wazuh_offline":
                assert status != "safe_to_open"
                assert confidence < 100
                assert report.coverage.coverage_pct < 100
            elif scenario == "no_telemetry":
                assert status != "safe_to_open"
                assert confidence < 70
            elif scenario == "partial_visibility":
                assert report.coverage.coverage_pct < 100
                
            results[scenario] = "PASSED"
            
    except AssertionError as e:
        print(f"FAILED on {scenario}")
        import traceback
        traceback.print_exc()
        results[scenario] = "FAILED"
    except Exception as e:
        print(f"ERROR on {scenario}: {e}")
        import traceback
        traceback.print_exc()
        results[scenario] = "ERROR"
    finally:
        db.close()
        
    print("\\n=== SPRINT 2 VALIDATION SUMMARY ===")
    for s, r in results.items():
        print(f"{s.ljust(25)}: {r}")

if __name__ == "__main__":
    run_tests()
