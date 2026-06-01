import os
import sys

# Add the app directory to the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db, Base
from app.core.auth import require_auth, User

# Create a clean in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_require_auth():
    # Return a dummy user with a known org_id
    class DummyUser:
        uid = "test_admin_user"
        email = "admin@example.com"
        role = "org_admin"
        org_id = "test_org_id"
        
    return DummyUser()

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[require_auth] = override_require_auth

client = TestClient(app)

def test_missing_org_id():
    response = client.post(
        "/api/v1/connectors/wazuh/connect",
        json={
            "manager_host": "wazuh.local",
            "port": 55000,
            "credentials": "supersecretkey"
        }
    )
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    print("Success: Missing org_id was rejected.")
    
def test_valid_payload():
    response = client.post(
        "/api/v1/connectors/wazuh/connect",
        json={
            "org_id": "test_org_id",
            "manager_host": "wazuh.local",
            "port": 55000,
            "credentials": "supersecretkey"
        }
    )
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code} - {response.text}"
    data = response.json()
    assert data["connector_type"] == "wazuh"
    print("Success: Valid payload was accepted and connector returned.")

if __name__ == "__main__":
    print("Running Tests...")
    test_missing_org_id()
    test_valid_payload()
    print("All tests passed!")
