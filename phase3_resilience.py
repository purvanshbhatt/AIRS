import sys
import unittest.mock as mock
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.organization import Organization
from sqlalchemy.exc import OperationalError

def run_resilience():
    client = TestClient(app)
    
    # 1. DB Unavailable Simulation
    print("Testing DB Unavailable...")
    with mock.patch("app.api.clinic.router.get_db", side_effect=OperationalError("mock", "mock", "mock")):
        resp = client.get("/api/clinic/readiness/test-org")
        assert resp.status_code != 500, f"Expected graceful failure, got 500: {resp.text}"

    # We need a valid org for the rest
    db = SessionLocal()
    org_id = "demo-org-123"
    
    # 2. Connector Timeout / Malformed / Offline Simulation
    print("Testing Connector Timeout...")
    # Mocking the ReadinessEngine or TrustEngine or EvidenceProvider
    # The simplest way is to mock fetch_events
    with mock.patch("app.services.clinic_engine.v2.readiness_engine.ReadinessEngine.evaluate", side_effect=Exception("Timeout or Malformed Data")):
        resp = client.get(f"/api/clinic/readiness/{org_id}")
        assert resp.status_code != 500, f"Expected graceful failure, got 500: {resp.text}"
        
    print("All resilience tests passed!")

if __name__ == "__main__":
    run_resilience()
