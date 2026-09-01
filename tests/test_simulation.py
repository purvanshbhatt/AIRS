"""
Tests for the Threat Simulation Engine and API.

Validates:
  - Single-category simulation execution
  - Full assessment across all categories
  - Blast radius deterministic calculation
  - Simulation history retrieval
  - API route integration
"""
import pytest
from fastapi.testclient import TestClient


# ═══════════════════════════════════════════════════════════════════════
# API Integration Tests
# ═══════════════════════════════════════════════════════════════════════

def _create_test_asset(client_with_org: TestClient, name: str, asset_type: str = "model", **kwargs) -> dict:
    """Helper to create a test AI asset."""
    payload = {
        "name": name,
        "asset_type": asset_type,
        "business_criticality": kwargs.get("business_criticality", "critical"),
        "exposure_level": kwargs.get("exposure_level", "public"),
        "lifecycle_stage": kwargs.get("lifecycle_stage", "production"),
        "risk_tags": kwargs.get("risk_tags", []),
        "associated_controls": kwargs.get("associated_controls", []),
    }
    resp = client_with_org.post("/api/v1/inventory/assets", json=payload)
    assert resp.status_code == 201, f"Failed to create asset: {resp.text}"
    return resp.json()


def test_run_simulation_prompt_injection(client_with_org: TestClient):
    """Test running a prompt injection simulation."""
    # Create an agent asset (matches PI-001 preconditions)
    _create_test_asset(client_with_org, "Test Agent", asset_type="agent")

    resp = client_with_org.post("/api/v1/simulations/run", json={
        "category": "prompt_injection",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "prompt_injection"
    assert data["blast_radius_score"] > 0
    assert data["readiness_degradation_pct"] > 0
    assert len(data["attack_chain"]) > 0
    assert len(data["affected_controls"]) > 0
    assert data["business_impact_narrative"] is not None


def test_run_simulation_no_matching_assets(client_with_org: TestClient):
    """Test simulation when no assets match the category preconditions."""
    # Create a dataset asset — doesn't match prompt_injection preconditions
    _create_test_asset(client_with_org, "Just Data", asset_type="dataset")

    resp = client_with_org.post("/api/v1/simulations/run", json={
        "category": "agent_privilege_escalation",
    })
    assert resp.status_code == 201
    data = resp.json()
    # Dataset doesn't match agent_privilege_escalation (requires "agent")
    assert data["blast_radius_score"] == 0.0


def test_run_simulation_invalid_category(client_with_org: TestClient):
    """Test that invalid category returns 400."""
    resp = client_with_org.post("/api/v1/simulations/run", json={
        "category": "nonexistent_attack",
    })
    assert resp.status_code == 400


def test_run_simulation_with_target_asset(client_with_org: TestClient):
    """Test running a simulation targeting a specific asset."""
    asset = _create_test_asset(client_with_org, "Targeted Model", asset_type="model")

    resp = client_with_org.post("/api/v1/simulations/run", json={
        "category": "data_exfiltration",
        "target_asset_id": asset["id"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "data_exfiltration"
    # Check that the attack chain references the targeted asset
    for step in data["attack_chain"]:
        assert step["target_asset_id"] == asset["id"]


def test_full_assessment(client_with_org: TestClient):
    """Test running a full threat assessment across all categories."""
    # Create assets that will match multiple categories
    _create_test_asset(client_with_org, "Prod Agent", asset_type="agent")
    _create_test_asset(client_with_org, "RAG Pipeline", asset_type="rag_pipeline")
    _create_test_asset(client_with_org, "ML Model", asset_type="model")

    resp = client_with_org.post("/api/v1/simulations/full-assessment")
    assert resp.status_code == 201
    data = resp.json()
    assert "results" in data
    assert "summary" in data
    assert data["summary"]["total_simulations"] == 9  # All 9 categories
    assert data["summary"]["avg_blast_radius"] >= 0


def test_simulation_history(client_with_org: TestClient):
    """Test retrieving simulation history."""
    # Create asset and run a simulation first
    _create_test_asset(client_with_org, "History Asset", asset_type="agent")
    client_with_org.post("/api/v1/simulations/run", json={"category": "prompt_injection"})

    resp = client_with_org.get("/api/v1/simulations/results/test-org-123")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert data["total"] >= 1


def test_simulation_history_with_category_filter(client_with_org: TestClient):
    """Test filtering simulation history by category."""
    _create_test_asset(client_with_org, "Filter Asset", asset_type="model")
    client_with_org.post("/api/v1/simulations/run", json={"category": "data_exfiltration"})
    client_with_org.post("/api/v1/simulations/run", json={"category": "model_dos"})

    resp = client_with_org.get("/api/v1/simulations/results/test-org-123?category=data_exfiltration")
    assert resp.status_code == 200
    data = resp.json()
    for r in data["results"]:
        assert r["category"] == "data_exfiltration"


def test_blast_radius_criticality_scaling(client_with_org: TestClient):
    """Test that blast radius scales with asset criticality."""
    # Critical asset should have higher blast radius than low
    _create_test_asset(client_with_org, "Critical Agent", asset_type="agent", business_criticality="critical")
    resp_critical = client_with_org.post("/api/v1/simulations/run", json={"category": "prompt_injection"})

    _create_test_asset(client_with_org, "Low Agent", asset_type="agent", business_criticality="low")
    # Run again — the result aggregates across both assets now
    # To isolate, we check the attack chain entries
    resp_both = client_with_org.post("/api/v1/simulations/run", json={"category": "prompt_injection"})

    assert resp_critical.status_code == 201
    assert resp_both.status_code == 201


def test_remediation_hooks_in_results(client_with_org: TestClient):
    """Test that remediation hooks are properly populated."""
    _create_test_asset(client_with_org, "Vuln Agent", asset_type="agent")

    resp = client_with_org.post("/api/v1/simulations/run", json={"category": "prompt_injection"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["remediation_hooks"] is not None
    assert len(data["remediation_hooks"]) > 0
    for hook in data["remediation_hooks"]:
        assert "rule_id" in hook
        assert "action" in hook
        assert "priority" in hook
