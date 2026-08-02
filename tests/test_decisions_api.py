import pytest
from app.schemas.decision import DecisionAction, ProjectReadinessRequest
from app.models.organization import Organization

@pytest.fixture
def setup_org(db_session):
    org = Organization(id="test_org_id", name="Test Org")
    db_session.add(org)
    db_session.commit()
    return org

def test_project_readiness_api(client, setup_org):
    req = ProjectReadinessRequest(
        actions=[
            DecisionAction(type="REMEDIATE_LIFECYCLE", software_name="Windows Server 2012")
        ]
    )
    
    resp = client.post("/api/v1/decisions/project/test_org_id", json=req.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    assert "assessment_score" in data
    assert "final_readiness" in data
    assert "readiness_delta" in data
    
def test_project_readiness_api_too_many_actions(client, setup_org):
    # Cap is 50
    actions = [DecisionAction(type="IMPROVE_ASSESSMENT", score_increase=1.0).model_dump() for _ in range(51)]
    resp = client.post("/api/v1/decisions/project/test_org_id", json={"actions": actions})
    assert resp.status_code == 422 # Pydantic max_length validation fails

def test_recommended_actions_api(client, setup_org):
    resp = client.get("/api/v1/decisions/recommended-actions/test_org_id")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
