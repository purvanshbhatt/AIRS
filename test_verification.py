import asyncio
from app.db.database import SessionLocal
from app.services.control_verification import VerificationService
from app.models.organization import Organization
from app.models.telemetry_event import TelemetryEvent
from app.models.connector import Connector
import uuid

async def test_verification_engine():
    db = SessionLocal()
    try:
        # Create a mock organization
        org_id = str(uuid.uuid4())
        org = Organization(id=org_id, name="Test Org", owner_uid="test_user")
        db.add(org)
        db.commit()
        
        svc = VerificationService(db, org_id)
        
        # Test 1: Ingest passing telemetry
        print("Test 1: Ingest passing telemetry for AC-1")
        result1 = svc.ingest_telemetry(control_id="AC-1", status="PASS")
        print(f"  -> State: {result1.state.value}, Confidence: {result1.confidence_level.value}")
        
        # Test 2: Attest a control
        print("Test 2: Attest to control AU-2")
        result2 = svc.attest_control(control_id="AU-2", user_id="test_user", reason="We do this manually")
        print(f"  -> State: {result2.state.value}, Confidence: {result2.confidence_level.value}")
        
        # Test 3: Attest a verified control (should not downgrade)
        print("Test 3: Attest to verified control AC-1")
        result3 = svc.attest_control(control_id="AC-1", user_id="test_user", reason="Trying to override")
        print(f"  -> State: {result3.state.value}, Confidence: {result3.confidence_level.value}")
        
        # Test 4: Ingest failing telemetry for a verified control
        print("Test 4: Ingest failing telemetry for AC-1")
        result4 = svc.ingest_telemetry(control_id="AC-1", status="FAIL")
        print(f"  -> State: {result4.state.value}, Confidence: {result4.confidence_level.value}")
        # Note: AC-1 will still be verified because the `any(status == "PASS")` rule applies across all historical evidence in this mock. Wait, yes, the historical evidence PASS is still there. Let's see.
        
        # Test 5: Summary
        print("Test 5: Summary")
        summary = svc.get_summary()
        print(summary)
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_verification_engine())
