def test_llm_health_contract_fields(client):
    response = client.get('/health/llm')
    assert response.status_code == 200

    data = response.json()
    assert 'llm_enabled' in data
    assert 'demo_mode' in data
    assert 'runtime_check' in data

    runtime_check = data['runtime_check']
    assert 'sdk_installed' in runtime_check
    assert 'credentials_configured' in runtime_check
    assert 'client_configured' in runtime_check


def test_health_includes_product_metadata(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data.get('status') == 'ok'
    assert 'product' in data
    assert data['product'].get('name')
    assert 'version' in data['product']
