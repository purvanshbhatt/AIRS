def test_root(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"].startswith("Welcome to")


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["product"]["name"]


def test_system_health(client):
    response = client.get("/health/system")
    assert response.status_code == 200
    payload = response.json()
    assert "version" in payload
    assert payload["environment"] in {"local", "staging", "prod"}
    assert "llm_enabled" in payload
    assert "demo_mode" in payload
    assert "integrations_enabled" in payload
    assert "last_deployment_at" in payload
