def test_create_pilot_request(client):
    response = client.post(
        "/api/pilot-request",
        json={
            "company_name": "Acme Security",
            "team_size": "51-200",
            "current_security_tools": "Splunk, CrowdStrike",
            "email": "security@acme.example",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["company_name"] == "Acme Security"
    assert payload["team_size"] == "51-200"
    assert payload["email"] == "security@acme.example"
    assert "id" in payload
    assert "created_at" in payload

