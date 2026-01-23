import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.roadmap_item import RoadmapItem
from app.models.organization import Organization

def test_roadmap_crud(client, db_session: Session):
    # 1. Create Organization
    org = Organization(name="Roadmap Test Org", owner_uid="dev-user")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    
    org_id = org.id
    
    # 2. Create Roadmap Item
    item_data = {
        "title": "Fix critical vulnerability",
        "description": "Patch server",
        "status": "todo",
        "priority": "high",
        "effort": "low"
    }
    
    response = client.post(f"/api/orgs/{org_id}/roadmap", json=item_data, headers={"Authorization": "Bearer mock-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == item_data["title"]
    assert data["organization_id"] == org_id
    item_id = data["id"]
    
    # 3. List Items
    response = client.get(f"/api/orgs/{org_id}/roadmap", headers={"Authorization": "Bearer mock-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == item_id
    
    # 4. Update Item
    update_data = {"status": "in_progress"}
    response = client.patch(f"/api/roadmap/{item_id}", json=update_data, headers={"Authorization": "Bearer mock-token"})
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    
    # 5. Delete Item
    response = client.delete(f"/api/roadmap/{item_id}", headers={"Authorization": "Bearer mock-token"})
    assert response.status_code == 204
    
    # Verify deletion
    response = client.get(f"/api/orgs/{org_id}/roadmap", headers={"Authorization": "Bearer mock-token"})
    assert response.json()["total"] == 0

def test_trend_endpoint(client, db_session: Session):
    # Create Org
    org = Organization(name="Trend Test Org", owner_uid="dev-user")
    db_session.add(org)
    db_session.commit()
    
    # Call trend endpoint (should be empty initially)
    response = client.get(f"/api/orgs/{org.id}/trend", headers={"Authorization": "Bearer mock-token"})
    assert response.status_code == 200
    assert response.json() == []

