"""
Tests for POST /api/v1/pilot-leads — enterprise pilot programme intake endpoint.
"""

import pytest

VALID_LEAD = {
    "contact_name": "Jane Smith",
    "company_name": "Acme Corp",
    "email": "jane@acme.example",
    "industry": "Technology / SaaS",
    "company_size": "51-200",
    "team_size": "5-10",
    "current_security_tools": "Splunk, CrowdStrike, Wiz",
    "ai_usage_description": "We deploy internal LLM copilots and use AI-assisted CI/CD.",
}


def test_enterprise_pilot_lead_created(client):
    """POST with full payload should return HTTP 201."""
    response = client.post("/api/v1/pilot-leads", json=VALID_LEAD)
    assert response.status_code == 201, response.text


def test_enterprise_pilot_lead_contact_name_persisted(client):
    """contact_name should be present in the response payload."""
    response = client.post("/api/v1/pilot-leads", json=VALID_LEAD)
    data = response.json()
    assert data.get("contact_name") == "Jane Smith"


def test_enterprise_pilot_lead_required_fields_only(client):
    """Minimal payload (contact_name + company_name + email) should succeed."""
    response = client.post(
        "/api/v1/pilot-leads",
        json={
            "contact_name": "Bob Lee",
            "company_name": "Minimal Co",
            "email": "bob@minimal.example",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "Minimal Co"


def test_enterprise_pilot_lead_has_id(client):
    """Created record should include an id field."""
    response = client.post("/api/v1/pilot-leads", json=VALID_LEAD)
    data = response.json()
    assert "id" in data


def test_enterprise_pilot_lead_has_created_at(client):
    """Created record should include a created_at timestamp."""
    response = client.post("/api/v1/pilot-leads", json=VALID_LEAD)
    data = response.json()
    assert "created_at" in data


def test_enterprise_pilot_lead_no_auth_required(client):
    """Pilot leads endpoint is public — no auth token should be needed."""
    response = client.post("/api/v1/pilot-leads", json=VALID_LEAD)
    assert response.status_code not in (401, 403)


def test_enterprise_pilot_lead_ai_usage_persisted(client):
    """ai_usage_description optional field should round-trip correctly."""
    response = client.post("/api/v1/pilot-leads", json=VALID_LEAD)
    data = response.json()
    assert data.get("ai_usage_description") == VALID_LEAD["ai_usage_description"]
