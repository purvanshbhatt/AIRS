"""
Tests for GET /api/v1/methodology — transparent scoring methodology endpoint.
"""

import pytest


def test_get_methodology_returns_200(client):
    """Methodology endpoint should return HTTP 200."""
    response = client.get("/api/v1/methodology")
    assert response.status_code == 200


def test_get_methodology_has_rubric_version(client):
    """Response must include rubric_version field."""
    response = client.get("/api/v1/methodology")
    data = response.json()
    assert "rubric_version" in data


def test_get_methodology_has_domains(client):
    """Response must include a non-empty domains list."""
    response = client.get("/api/v1/methodology")
    data = response.json()
    assert "domains" in data
    assert isinstance(data["domains"], list)
    assert len(data["domains"]) > 0


def test_get_methodology_domain_structure(client):
    """Each domain entry should have domain_id, domain_name, and weight_pct fields."""
    response = client.get("/api/v1/methodology")
    data = response.json()
    for domain in data["domains"]:
        assert "domain_id" in domain, f"Domain missing 'domain_id': {domain}"
        assert "domain_name" in domain, f"Domain missing 'domain_name': {domain}"
        assert "weight_pct" in domain, f"Domain missing 'weight_pct': {domain}"


def test_get_methodology_no_auth_required(client):
    """Methodology is a public endpoint — no auth token required."""
    # client has AUTH_REQUIRED=false globally, but confirming no 401/403 edge case
    response = client.get("/api/v1/methodology")
    assert response.status_code not in (401, 403)
