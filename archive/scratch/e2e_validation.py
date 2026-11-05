import os
os.environ["ENV"] = "local"
import sys
import json
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch

# Add app to path FIRST
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock out Firestore syncs entirely
patch("app.db.firestore.firestore_save_assessment", return_value=True).start()
patch("app.db.firestore.firestore_save_org", return_value=True).start()
patch("app.db.firestore.require_firestore", return_value=True).start()
patch("app.db.firestore.is_firestore_available", return_value=False).start()

from app.db.database import SessionLocal
from app.models.organization import Organization
from app.models.assessment import Assessment, AssessmentStatus
from app.models.finding import Finding
from app.models.finding_provenance import FindingProvenance
from app.models.score import Score
from app.models.score_audit_log import ScoreAuditLog
from app.models.tech_stack import TechStackItem

from app.services.assessment import AssessmentService
from app.services.integrations import IntegrationService

def run_validation():
    db = SessionLocal()
    
    print("========================================")
    print("E2E VALIDATION: Assessment -> Telemetry -> Score")
    print("========================================\n")
    
    org_id = str(uuid4())
    print(f"1. Creating Test Organization (ID: {org_id})")
    org = Organization(
        id=org_id,
        name="Validation Test Org",
        industry="Technology",
        size="50-200"
    )
    db.add(org)
    
    # Add minimal tech stack to avoid 0 scores
    tech = TechStackItem(
        id=str(uuid4()),
        org_id=org_id,
        component_name="Splunk Enterprise Security",
        version="9.0.0",
        category="SIEM",
        lts_status="active",
        major_versions_behind=0
    )
    db.add(tech)
    db.commit()
    
    print("2. Starting Quick Assessment")
    assessment_service = AssessmentService(db)
    assessment = assessment_service.start(org_id)
    assessment_id = assessment.id
    print(f"   Assessment ID: {assessment_id}")
    
    # Check DB score before
    print("\n[VALIDATION #1: Score Before Completion]")
    assessment_db = db.query(Assessment).filter_by(id=assessment_id).first()
    print(f"   DB overall_score: {assessment_db.overall_score}")
    
    # Let's hit the GHI endpoint using the function directly to see the API response payload
    from app.services.governance.validation_engine import validate_organization
    org_db = db.query(Organization).filter_by(id=org_id).first()
    ghi_before = validate_organization(db, org_db)
    print(f"   API GHI Score (Readiness): {getattr(ghi_before, 'ghi', getattr(ghi_before, 'overall_score', ghi_before))}")
    
    print("\n3. Submitting Assessment Answers and Computing Score")
    # Submit some dummy answers to generate findings
    from app.schemas.assessment import AnswerInput
    answers = [
        AnswerInput(question_id="si_01", value="no", notes=""),
        AnswerInput(question_id="ia_01", value="partial", notes=""),
    ]
    assessment_service.submit_answers(assessment_id, answers)
    assessment_service.compute_score(assessment_id)
    
    # Check DB score after
    print("\n[VALIDATION #1: Score After Completion]")
    assessment_db = db.query(Assessment).filter_by(id=assessment_id).first()
    print(f"   DB overall_score: {assessment_db.overall_score}")
    
    org_db = db.query(Organization).filter_by(id=org_id).first()
    ghi_after = validate_organization(db, org_db)
    print(f"   API GHI Score (Readiness): {getattr(ghi_after, 'ghi', getattr(ghi_after, 'overall_score', ghi_after))}")
    
    findings = db.query(Finding).filter_by(assessment_id=assessment_id).all()
    print(f"   Generated {len(findings)} Findings:")
    for f in findings:
        print(f"     - [{f.id}] {f.title} (Severity: {getattr(f.severity, 'value', f.severity)})")
    
    print("\n4. Injecting SIEM Telemetry (Splunk Seed)")
    integration_service = IntegrationService(db)
    integration_service.seed_mock_splunk_findings(org_id)
    
    print("\n[VALIDATION #3: Score After Telemetry Injection]")
    db.expire_all() # Refresh session
    
    assessment_db = db.query(Assessment).filter_by(id=assessment_id).first()
    print(f"   DB overall_score: {assessment_db.overall_score}")
    
    org_db = db.query(Organization).filter_by(id=org_id).first()
    ghi_telemetry = validate_organization(db, org_db)
    print(f"   API GHI Score (Readiness): {getattr(ghi_telemetry, 'ghi', getattr(ghi_telemetry, 'overall_score', ghi_telemetry))}")
    
    # Check provenance
    provenance = db.query(FindingProvenance).join(Finding).filter(Finding.assessment_id == assessment_id).all()
    print(f"   Created {len(provenance)} FindingProvenance records:")
    for p in provenance:
        print(f"     - Finding ID: {p.finding_id} | Status: {p.verification_status}")
    
    # Check audit logs
    logs = db.query(ScoreAuditLog).filter_by(assessment_id=assessment_id).all()
    print(f"\n   Score Audit Logs:")
    for log in logs:
        print(f"     - Score changed from {log.previous_score} to {log.new_score} ({log.trigger_event})")

if __name__ == "__main__":
    run_validation()
