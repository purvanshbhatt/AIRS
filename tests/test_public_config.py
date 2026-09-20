"""
Tests for Public Product Configuration API (M1: Host- and Route-Aware Vertical Architecture).
"""

import ast
import pytest
from app.api.public import VERTICAL_CONFIGS, resolve_vertical_key


def test_public_config_default(client):
    """Default request with no parameters returns the general vertical configuration."""
    response = client.get("/api/public/product-config")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["vertical_key"] == "general"
    assert data["display_name"] == "ResilAI"
    assert data["industry_label"] == "Enterprise & Cloud"
    assert "AI Incident Readiness Platform" in data["headline"]
    assert "ready" in data["core_question"]
    assert isinstance(data["focus_areas"], list)
    assert len(data["focus_areas"]) >= 3
    assert data["demo_org_id"] == "demo-acme-technologies"
    assert data["demo_org_name"] == "Acme Technologies"


def test_public_config_query_healthcare(client):
    """Query parameter vertical=healthcare returns healthcare vertical configuration."""
    response = client.get("/api/public/product-config?vertical=healthcare")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["vertical_key"] == "healthcare"
    assert data["display_name"] == "ResilAI Healthcare"
    assert data["industry_label"] == "Healthcare"
    assert "healthcare organizations" in data["headline"]
    assert "ransomware" in data["core_question"].lower()
    assert data["demo_org_id"] == "demo-northstar-health"
    assert data["demo_org_name"] == "Northstar Family Health"
    assert any("EHR" in area for area in data["focus_areas"])
    assert any("Veeam" in area for area in data["focus_areas"])


def test_public_config_query_legal(client):
    """Query parameter vertical=legal returns legal vertical configuration."""
    response = client.get("/api/public/product-config?vertical=legal")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["vertical_key"] == "legal"
    assert data["display_name"] == "ResilAI Legal"
    assert data["industry_label"] == "Law Firms & Legal"
    assert "law firms" in data["headline"]
    assert "client data" in data["core_question"].lower()
    assert data["demo_org_id"] == "demo-northstar-cole"
    assert data["demo_org_name"] == "Northstar & Cole LLP"
    assert any("Client data protection" in area for area in data["focus_areas"])
    assert any("ABA" in area for area in data["focus_areas"])


def test_public_config_unknown_fallback(client):
    """Unknown vertical key falls back gracefully to general."""
    response = client.get("/api/public/product-config?vertical=finance")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["vertical_key"] == "general"
    assert data["demo_org_id"] == "demo-acme-technologies"


def test_public_config_header_routing(client):
    """X-ResilAI-Vertical header routes to specified vertical."""
    response = client.get("/api/public/product-config", headers={"X-ResilAI-Vertical": "healthcare"})
    assert response.status_code == 200, response.text
    assert response.json()["vertical_key"] == "healthcare"

    response = client.get("/api/public/product-config", headers={"X-ResilAI-Vertical": "legal"})
    assert response.status_code == 200, response.text
    assert response.json()["vertical_key"] == "legal"


def test_public_config_host_subdomain_routing(client):
    """Host header subdomain routes to specified vertical."""
    response = client.get("/api/public/product-config", headers={"Host": "healthcare.staging.resilai.org"})
    assert response.status_code == 200, response.text
    assert response.json()["vertical_key"] == "healthcare"

    response = client.get("/api/public/product-config", headers={"Host": "legal.staging.resilai.org"})
    assert response.status_code == 200, response.text
    assert response.json()["vertical_key"] == "legal"

    response = client.get("/api/public/product-config", headers={"Host": "staging.resilai.org"})
    assert response.status_code == 200, response.text
    assert response.json()["vertical_key"] == "general"


def test_public_config_precedence(client):
    """Query parameter takes precedence over header and subdomain."""
    # Query is legal, header is healthcare, host is healthcare
    response = client.get(
        "/api/public/product-config?vertical=legal",
        headers={"X-ResilAI-Vertical": "healthcare", "Host": "healthcare.staging.resilai.org"},
    )
    assert response.status_code == 200
    assert response.json()["vertical_key"] == "legal"


def test_resolve_vertical_key_unit():
    """Test pure resolution logic directly."""
    assert resolve_vertical_key("healthcare") == "healthcare"
    assert resolve_vertical_key(query_param="legal") == "legal"
    assert resolve_vertical_key(header_val="healthcare") == "healthcare"
    assert resolve_vertical_key(host="healthcare.staging.resilai.org:443") == "healthcare"
    assert resolve_vertical_key(host="legal.staging.resilai.org") == "legal"
    assert resolve_vertical_key(host="healthcare-staging.web.app") == "healthcare"
    assert resolve_vertical_key(host="legal-staging.web.app") == "legal"
    assert resolve_vertical_key(query_param=None, header_val=None, host=None) == "general"


def test_no_llm_imports_in_public_config():
    """Architectural invariant R4: Ensure app.api.public has no LLM or intelligence imports."""
    with open("app/api/public.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename="app/api/public.py")

    forbidden = ["google.genai", "google.generativeai", "ai_narrative", "llm_narrative", "app.services.intelligence"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for hint in forbidden:
                    assert hint not in alias.name, f"Forbidden LLM import detected in public config: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for hint in forbidden:
                assert hint not in mod, f"Forbidden LLM import detected in public config: {mod}"
