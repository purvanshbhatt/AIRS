"""
E2E Test Suite: Multi-Vertical Positioning & Public Config Contract
Validates:
- Requirement R1 & Feature F4: GET /api/public/product-config
- Precedence: Query params -> Header -> Host subdomain -> Default
- Boundary cases: Unknown vertical, mixed case, whitespace, special chars
- Requirement R4: Shared Deterministic Scoring Engine invariant (AST isolation, zero duplicate engines)
"""

import ast
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.api.public import VERTICAL_CONFIGS, resolve_vertical_key


@pytest.fixture(scope="module")
def client():
    """Create test client for public config testing."""
    return TestClient(app)


# ==============================================================================
# Tier 1: Feature F4 — Public Config API Contract Tests
# ==============================================================================

class TestPublicConfigContract:
    """Validate GET /api/public/product-config adheres to interface contract."""

    def test_default_returns_general_vertical(self, client):
        """Test F4.01: Unparameterized GET returns general vertical configuration."""
        response = client.get("/api/public/product-config")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "general"
        assert data["display_name"] == "ResilAI"
        assert data["industry_label"] == "Enterprise & Cloud"
        assert "AI Incident Readiness Platform" in data["headline"]
        assert "security or AI incident" in data["core_question"]
        assert isinstance(data["focus_areas"], list)
        assert len(data["focus_areas"]) > 0
        assert data["demo_org_id"] == "demo-acme-technologies"
        assert data["demo_org_name"] == "Acme Technologies"

    def test_healthcare_query_param(self, client):
        """Test F4.02: ?vertical=healthcare returns healthcare vertical configuration."""
        response = client.get("/api/public/product-config?vertical=healthcare")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "healthcare"
        assert data["display_name"] == "ResilAI Healthcare"
        assert data["industry_label"] == "Healthcare"
        assert "healthcare organizations" in data["headline"]
        assert "ransomware hits your clinic" in data["core_question"]
        assert any("Ransomware" in fa for fa in data["focus_areas"])
        assert any("EHR" in fa for fa in data["focus_areas"])
        assert any("Veeam" in fa for fa in data["focus_areas"])
        assert data["demo_org_id"] == "demo-northstar-health"
        assert data["demo_org_name"] == "Northstar Family Health"

    def test_legal_query_param(self, client):
        """Test F4.03: ?vertical=legal returns legal vertical configuration."""
        response = client.get("/api/public/product-config?vertical=legal")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "legal"
        assert data["display_name"] == "ResilAI Legal"
        assert data["industry_label"] == "Law Firms & Legal"
        assert "law firms" in data["headline"]
        assert "protect client data" in data["core_question"]
        assert any("Client data protection" in fa for fa in data["focus_areas"])
        assert any("Privileged access" in fa for fa in data["focus_areas"])
        assert data["demo_org_id"] == "demo-northstar-cole"
        assert data["demo_org_name"] == "Northstar & Cole LLP"

    def test_header_resolution(self, client):
        """Test F4.04: X-ResilAI-Vertical header sets active vertical."""
        response = client.get(
            "/api/public/product-config",
            headers={"X-ResilAI-Vertical": "healthcare"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "healthcare"
        assert data["demo_org_id"] == "demo-northstar-health"

    def test_query_param_overrides_header(self, client):
        """Test F4.05: Query parameter takes precedence over header."""
        response = client.get(
            "/api/public/product-config?vertical=legal",
            headers={"X-ResilAI-Vertical": "healthcare"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "legal"
        assert data["demo_org_id"] == "demo-northstar-cole"


# ==============================================================================
# Tier 2: Boundary, Precedence & Adversarial Cases
# ==============================================================================

class TestPublicConfigBoundaries:
    """Validate edge cases, unknown inputs, subdomains, and normalization."""

    def test_unknown_vertical_fallback(self, client):
        """Test T2.01: Unknown vertical string safely defaults to general."""
        response = client.get("/api/public/product-config?vertical=finance")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "general"
        assert data["demo_org_id"] == "demo-acme-technologies"

    def test_mixed_case_query_param(self, client):
        """Test T2.02: Mixed-case query parameters are normalized."""
        for v_input, expected in [
            ("HEALTHCARE", "healthcare"),
            ("LeGaL", "legal"),
            ("GeNeRaL", "general"),
        ]:
            response = client.get(f"/api/public/product-config?vertical={v_input}")
            assert response.status_code == 200
            assert response.json()["vertical_key"] == expected

    def test_whitespace_padded_query(self, client):
        """Test T2.03: Whitespace in query param is trimmed."""
        response = client.get("/api/public/product-config?vertical=%20healthcare%20")
        assert response.status_code == 200
        assert response.json()["vertical_key"] == "healthcare"

    def test_subdomain_resolution_via_host_header(self, client):
        """Test T2.04: Subdomains in Host header resolve correctly."""
        # Healthcare subdomain
        res_hc = client.get(
            "/api/public/product-config",
            headers={"Host": "healthcare.staging.resilai.org"},
        )
        assert res_hc.status_code == 200
        assert res_hc.json()["vertical_key"] == "healthcare"

        # Legal subdomain
        res_leg = client.get(
            "/api/public/product-config",
            headers={"Host": "legal.staging.resilai.org"},
        )
        assert res_leg.status_code == 200
        assert res_leg.json()["vertical_key"] == "legal"

        # General staging subdomain
        res_stg = client.get(
            "/api/public/product-config",
            headers={"Host": "staging.resilai.org"},
        )
        assert res_stg.status_code == 200
        assert res_stg.json()["vertical_key"] == "general"

    def test_query_param_overrides_host_subdomain(self, client):
        """Test T2.05: Query parameter takes precedence over Host subdomain."""
        response = client.get(
            "/api/public/product-config?vertical=legal",
            headers={"Host": "healthcare.staging.resilai.org"},
        )
        assert response.status_code == 200
        assert response.json()["vertical_key"] == "legal"

    def test_empty_and_special_char_query(self, client):
        """Test T2.06: Empty and malformed queries safely default to general."""
        for query in ["", "?vertical=", "?vertical=null", "?vertical=<script>"]:
            url = f"/api/public/product-config{query}"
            response = client.get(url)
            assert response.status_code == 200
            assert response.json()["vertical_key"] == "general"


# ==============================================================================
# Tier 4: Architectural Invariant R4 — Shared Deterministic Scoring Engine
# ==============================================================================

class TestArchitecturalInvariantR4:
    """Verify shared scoring engine integrity, AST LLM isolation, and zero duplicate engines."""

    def test_scoring_engine_centralized_definition(self):
        """Test R4.01: calculate_readiness_delta is defined in app.services.scoring."""
        from app.services.scoring import calculate_readiness_delta
        assert callable(calculate_readiness_delta)

    def test_scoring_engine_ast_llm_isolation(self):
        """Test R4.02: app/services/scoring.py has zero LLM or generative imports."""
        scoring_path = Path("/run/media/purvansh/Software/Projects/AIRS/app/services/scoring.py")
        assert scoring_path.exists(), "scoring.py must exist"

        with open(scoring_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename="scoring.py")

        forbidden_tokens = ["google.genai", "google.generativeai", "ai_narrative", "llm_narrative"]

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for forbidden in forbidden_tokens:
                        assert forbidden not in alias.name, f"Forbidden import found in scoring.py: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                for forbidden in forbidden_tokens:
                    assert forbidden not in module_name, f"Forbidden from-import in scoring.py: {module_name}"

    def test_zero_duplicate_scoring_engines(self):
        """Test R4.03: Zero duplicate scoring engine files exist in app/."""
        app_dir = Path("/run/media/purvansh/Software/Projects/AIRS/app")
        scoring_files = list(app_dir.rglob("*scoring*.py"))

        # The only valid scoring file is app/services/scoring.py and schema/api definitions
        for file_path in scoring_files:
            rel = str(file_path.relative_to(app_dir))
            # Must not be a vertical-specific scoring implementation
            assert "legal_scoring" not in rel, f"Duplicate scoring engine detected: {rel}"
            assert "healthcare_scoring" not in rel, f"Duplicate scoring engine detected: {rel}"
            assert "general_scoring" not in rel, f"Duplicate scoring engine detected: {rel}"

    def test_deterministic_scoring_calculation(self):
        """Test R4.04: Readiness delta calculation is pure and deterministic."""
        from app.services.scoring import calculate_readiness_delta

        # Run scoring calculation twice with identical parameters
        res1 = calculate_readiness_delta(
            assessment_score=75.0,
            verified_controls=[{"severity": "critical"}],
            verified_coverages=[],
            lifecycle_risks=[],
            exposure_risks=[],
            previous_readiness_score=70.0,
        )
        res2 = calculate_readiness_delta(
            assessment_score=75.0,
            verified_controls=[{"severity": "critical"}],
            verified_coverages=[],
            lifecycle_risks=[],
            exposure_risks=[],
            previous_readiness_score=70.0,
        )

        assert res1 == res2, "Scoring calculation must be strictly deterministic"
        assert res1["final_readiness"] == 78.0
        assert res1["readiness_delta"] == 8.0
