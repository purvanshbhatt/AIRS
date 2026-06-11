"""
Tests for the Governance Policy Engine and API.

Validates:
  - Policy CRUD operations
  - Deterministic policy evaluation
  - Violation detection
  - Enforcement mode behavior (enforce vs audit vs disabled)
  - Evaluation audit trail
  - API route integration
"""
import pytest
from fastapi.testclient import TestClient


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _create_test_asset(client: TestClient, name: str, asset_type: str = "model", **kwargs) -> dict:
    """Helper to create a test AI asset."""
    payload = {
        "name": name,
        "asset_type": asset_type,
        "business_criticality": kwargs.get("business_criticality", "critical"),
        "exposure_level": kwargs.get("exposure_level", "public"),
        "lifecycle_stage": kwargs.get("lifecycle_stage", "production"),
    }
    resp = client.post("/api/v1/inventory/assets", json=payload)
    assert resp.status_code == 201
    return resp.json()


def _create_test_policy(client: TestClient, name: str, rules: list, **kwargs) -> dict:
    """Helper to create a test governance policy."""
    payload = {
        "name": name,
        "policy_type": kwargs.get("policy_type", "deployment_gate"),
        "policy_definition": {"rules": rules},
        "enforcement_mode": kwargs.get("enforcement_mode", "enforce"),
        "description": kwargs.get("description", "Test policy"),
    }
    resp = client.post("/api/v1/policies", json=payload)
    assert resp.status_code == 201, f"Failed to create policy: {resp.text}"
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════
# Policy CRUD Tests
# ═══════════════════════════════════════════════════════════════════════

def test_create_policy(client: TestClient):
    """Test creating a governance policy."""
    resp = client.post("/api/v1/policies", json={
        "name": "AI Model Approval Required",
        "policy_type": "model_approval",
        "description": "All production models must have an approval record.",
        "policy_definition": {
            "rules": [
                {
                    "condition": "asset_type == 'model'",
                    "require": "lifecycle_stage != 'production'",
                    "severity": "critical",
                }
            ]
        },
        "enforcement_mode": "enforce",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "AI Model Approval Required"
    assert data["policy_type"] == "model_approval"
    assert data["enforcement_mode"] == "enforce"
    assert data["version"] == 1
    assert data["is_active"] is True


def test_create_policy_invalid_type(client: TestClient):
    """Test that invalid policy_type returns 400."""
    resp = client.post("/api/v1/policies", json={
        "name": "Bad Type",
        "policy_type": "nonexistent_type",
        "policy_definition": {"rules": []},
    })
    assert resp.status_code == 400


def test_create_policy_missing_rules(client: TestClient):
    """Test that policy_definition without 'rules' returns 400."""
    resp = client.post("/api/v1/policies", json={
        "name": "No Rules",
        "policy_type": "ai_usage",
        "policy_definition": {"something": "else"},
    })
    assert resp.status_code == 400


def test_list_policies(client: TestClient):
    """Test listing policies."""
    _create_test_policy(client, "Policy A", [])
    _create_test_policy(client, "Policy B", [])

    resp = client.get("/api/v1/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


def test_get_policy(client: TestClient):
    """Test getting a specific policy."""
    policy = _create_test_policy(client, "Get This Policy", [])

    resp = client.get(f"/api/v1/policies/{policy['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get This Policy"


def test_update_policy(client: TestClient):
    """Test updating a policy increments version."""
    policy = _create_test_policy(client, "Updatable Policy", [])
    assert policy["version"] == 1

    resp = client.patch(f"/api/v1/policies/{policy['id']}", json={
        "name": "Updated Policy Name",
        "enforcement_mode": "audit",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Policy Name"
    assert data["enforcement_mode"] == "audit"
    assert data["version"] == 2


# ═══════════════════════════════════════════════════════════════════════
# Policy Evaluation Tests
# ═══════════════════════════════════════════════════════════════════════

def test_evaluate_policy_pass(client: TestClient):
    """Test evaluating a policy that passes."""
    # Create an asset in development
    _create_test_asset(client, "Dev Model", asset_type="model", lifecycle_stage="development")

    # Create a policy that only triggers on production models
    policy = _create_test_policy(client, "Prod Only", [
        {
            "condition": "lifecycle_stage == 'production'",
            "require": "owner IS NOT NULL",
            "severity": "high",
        }
    ])

    resp = client.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "pass"
    assert len(data["violations"]) == 0


def test_evaluate_policy_fail_enforce(client: TestClient):
    """Test evaluating a policy in enforce mode that fails."""
    # Create a production model without an owner
    _create_test_asset(
        client, "Unowned Model", asset_type="model",
        lifecycle_stage="production",
    )

    # Policy requires owner for production models
    policy = _create_test_policy(client, "Owner Required", [
        {
            "condition": "lifecycle_stage == 'production'",
            "require": "owner IS NOT NULL",
            "severity": "critical",
        }
    ], enforcement_mode="enforce")

    resp = client.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "fail"
    assert len(data["violations"]) >= 1
    assert data["violations"][0]["severity"] == "critical"
    assert data["enforcement_mode"] == "enforce"


def test_evaluate_policy_warn_audit_mode(client: TestClient):
    """Test that violations in audit mode produce 'warn' instead of 'fail'."""
    _create_test_asset(
        client, "Audit Model", asset_type="model",
        lifecycle_stage="production",
    )

    policy = _create_test_policy(client, "Audit Only", [
        {
            "condition": "lifecycle_stage == 'production'",
            "require": "owner IS NOT NULL",
            "severity": "high",
        }
    ], enforcement_mode="audit")

    resp = client.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "warn"  # Not "fail" because mode is audit
    assert len(data["violations"]) >= 1


def test_evaluate_disabled_policy(client: TestClient):
    """Test that disabled policies always pass."""
    _create_test_asset(client, "Any Model", asset_type="model")

    policy = _create_test_policy(client, "Disabled Policy", [
        {
            "condition": "asset_type == 'model'",
            "require": "owner IS NOT NULL",
            "severity": "critical",
        }
    ], enforcement_mode="disabled")

    resp = client.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "pass"
    assert data["assets_evaluated"] == 0


def test_evaluate_all_policies(client: TestClient):
    """Test evaluating all active policies."""
    _create_test_asset(client, "All Eval Model", asset_type="model", lifecycle_stage="production")

    _create_test_policy(client, "Policy 1", [
        {"condition": "lifecycle_stage == 'production'", "require": "owner IS NOT NULL", "severity": "high"}
    ], enforcement_mode="enforce")
    _create_test_policy(client, "Policy 2", [], enforcement_mode="audit")

    resp = client.post("/api/v1/policies/evaluate-all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_policies"] >= 2
    assert "passing" in data
    assert "failing" in data
    assert "warning" in data


def test_policy_condition_in_operator(client: TestClient):
    """Test the IN operator in policy conditions."""
    _create_test_asset(client, "Agent Asset", asset_type="agent", lifecycle_stage="production")

    policy = _create_test_policy(client, "Type Gate", [
        {
            "condition": "asset_type IN ('agent', 'model')",
            "require": "business_criticality == 'critical'",
            "severity": "medium",
        }
    ])

    resp = client.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    # Agent with critical criticality should pass
    assert data["result"] == "pass"


def test_policy_evaluation_history(client: TestClient):
    """Test that evaluations are recorded in the audit trail."""
    _create_test_asset(client, "Audited Model", asset_type="model")
    policy = _create_test_policy(client, "Audited Policy", [])

    # Evaluate twice
    client.post(f"/api/v1/policies/{policy['id']}/evaluate")
    client.post(f"/api/v1/policies/{policy['id']}/evaluate")

    resp = client.get(f"/api/v1/policies/{policy['id']}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    for entry in data:
        assert entry["policy_id"] == policy["id"]
        assert "result" in entry
