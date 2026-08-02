import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.services.evidence.registry import get_instance, reset_instance
from app.services.evidence.base_adapter import EvidenceAdapter, AdapterHealth
from app.core.auth import User, require_auth

client = TestClient(app)

class MockAdapter(EvidenceAdapter):
    def __init__(self, name: str, health_res: AdapterHealth):
        self._name = name
        self._health = health_res

    @property
    def connector_name(self) -> str:
        return self._name

    async def fetch_evidence(self, *, since=None):
        return []

    def normalize(self, payload):
        return []

    async def health(self) -> AdapterHealth:
        return self._health

@pytest.fixture
def auth_override():
    # Override auth to return a valid user with an org_id
    def override_require_auth():
        user = User(uid="test_uid", email="test@example.com")
        user.org_id = "org_123"
        return user
    
    app.dependency_overrides[require_auth] = override_require_auth
    yield
    app.dependency_overrides.pop(require_auth, None)

@pytest.fixture
def auth_override_missing_org():
    # Override auth to return a valid user without org_id
    def override_require_auth():
        return User(uid="test_uid", email="test@example.com")
    
    app.dependency_overrides[require_auth] = override_require_auth
    yield
    app.dependency_overrides.pop(require_auth, None)

@pytest.fixture
def mock_registry():
    reset_instance()
    registry = get_instance()
    
    # Register a healthy adapter
    health1 = AdapterHealth(healthy=True, success_count=10, failure_count=0)
    adapter1 = MockAdapter("test-connector-1", health1)
    registry.register(adapter1)
    
    # Register an unhealthy adapter
    health2 = AdapterHealth(healthy=False, success_count=5, failure_count=5)
    adapter2 = MockAdapter("test-connector-2", health2)
    registry.register(adapter2)
    
    yield registry
    reset_instance()

def test_connectors_confidence_api_missing_org(auth_override_missing_org):
    response = client.get("/api/v1/connectors/confidence")
    assert response.status_code == 422
    assert "Missing org_id" in response.json()["error"]["message"]

def test_connectors_confidence_api_success(auth_override, mock_registry):
    response = client.get("/api/v1/connectors/confidence")
    assert response.status_code == 200
    data = response.json()
    
    assert data["org_id"] == "org_123"
    assert "aggregate_score" in data
    assert len(data["connectors"]) == 2
    
    connectors = {c["connector_name"]: c for c in data["connectors"]}
    
    assert "test-connector-1" in connectors
    assert connectors["test-connector-1"]["factors"]["uptime"] == 1.0
    
    assert "test-connector-2" in connectors
    assert connectors["test-connector-2"]["confidence_score"] == 0.0
    assert connectors["test-connector-2"]["factors"]["uptime"] == 0.0
