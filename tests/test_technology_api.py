import pytest

def test_get_technology_inventory_422():
    pass

def test_get_technology_inventory(client):
    response = client.get("/api/v1/technology/inventory/test_org")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_technology_lifecycle(client):
    response = client.get("/api/v1/technology/lifecycle/test_org")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_technology_exposure(client):
    response = client.get("/api/v1/technology/exposure/test_org")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_frameworks_coverage(client, db_session):
    from app.models.organization import Organization
    db_session.add(Organization(id="test_org", name="Test Org", owner_uid="dev-user"))
    db_session.add(Organization(id="other_org", name="Other", owner_uid="another-user"))
    db_session.commit()

    response = client.get("/api/v1/frameworks/coverage/test_org")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    # Coverage is only served to the organization's owner.
    assert client.get("/api/v1/frameworks/coverage/other_org").status_code == 404
