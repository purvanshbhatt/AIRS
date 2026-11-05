import pytest
from app.models.organization import Organization

def _make_org(db_session) -> str:
    org = Organization(id="test-org", name="Clinic Test Org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org.id

def test_clinic_readiness_endpoint(client, db_session):
    # Setup
    org_id = _make_org(db_session)
    
    # Request
    response = client.get(f"/api/clinic/readiness/{org_id}")
    
    # Assert
    assert response.status_code == 200, response.text
    data = response.json()
    
    # Assert new business product models are present
    assert "business_continuity" in data
    assert "operational_readiness" in data["business_continuity"]
    assert "estimated_downtime_minutes" in data["business_continuity"]["operational_readiness"]
    
    # Assert 'trust' has been renamed to 'verification'
    assert "verification" in data
    assert "trust" not in data
    
    # Check that failed checks use verification
    if data["failed_checks"]:
        check = data["failed_checks"][0]
        assert "verification" in check
        assert "trust" not in check
        
    # Check for leaked engineering terminology
    resp_str = response.text.lower()
    for term in ["capability", "evidence", "normalizedevent", "risk_score"]:
        assert term not in resp_str, f"Leaked engineering term: {term}"

def test_clinic_readiness_unknown_philosophy(client, db_session):
    # Setup production org (no demo data)
    org = Organization(id="prod-org", name="Clinic Prod Org", org_mode="production")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    
    # Request
    response = client.get(f"/api/clinic/readiness/{org.id}")
    
    # Assert
    assert response.status_code == 200, response.text
    data = response.json()
    
    # Assert degraded gracefully
    assert data["status"] == "unknown"
    assert "missing data" in data["summary"].lower()
    
    # Verify connectors list is empty (0 coverage)
    assert len(data.get("connectors", [])) == 0
