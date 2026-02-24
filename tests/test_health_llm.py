from app.core.config import settings


def test_llm_health_contract_fields(client):
    response = client.get('/health/llm')
    assert response.status_code == 200

    data = response.json()
    assert 'llm_enabled' in data
    assert 'demo_mode' in data
    assert 'runtime_check' in data

    runtime_check = data['runtime_check']
    assert 'sdk_installed' in runtime_check
    assert 'feature_flag_enabled' in runtime_check
    assert 'credentials_configured' in runtime_check
    assert 'auth_mode' in runtime_check
    assert 'client_configured' in runtime_check


def test_health_includes_product_metadata(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data.get('status') == 'ok'
    assert 'product' in data
    assert data['product'].get('name')
    assert 'version' in data['product']


def test_llm_health_enables_with_vertex_adc(monkeypatch, client):
    monkeypatch.setattr(settings, "AIRS_USE_LLM", True)
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    monkeypatch.setattr(settings, "GCP_PROJECT_ID", "gen-lang-client-0384513977")

    response = client.get('/health/llm')
    assert response.status_code == 200
    data = response.json()

    assert data["llm_enabled"] is True
    assert data["runtime_check"]["auth_mode"] == "vertex-adc"
