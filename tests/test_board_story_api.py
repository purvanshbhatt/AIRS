import pytest
from app.models.organization import Organization

@pytest.fixture
def setup_org(db_session):
    # Owned by the caller: the board story is only served to the organization's owner.
    org = Organization(id="test_org_id_reports", name="Test Org", owner_uid="dev-user")
    db_session.add(org)
    db_session.commit()
    return org

def test_get_board_story_success(client, setup_org):
    resp = client.get("/api/v1/reports/board-story?org_id=test_org_id_reports")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert len(data["sections"]) == 10

def test_get_board_story_not_found(client):
    resp = client.get("/api/v1/reports/board-story?org_id=nonexistent")
    assert resp.status_code == 404

def test_get_board_story_missing_org(client):
    resp = client.get("/api/v1/reports/board-story")
    assert resp.status_code == 422


def test_get_board_story_of_another_owner_is_not_served(client, db_session):
    db_session.add(Organization(id="someone_elses_org", name="Other", owner_uid="another-user"))
    db_session.commit()
    resp = client.get("/api/v1/reports/board-story?org_id=someone_elses_org")
    assert resp.status_code == 404
