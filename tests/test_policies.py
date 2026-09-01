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

def _create_test_asset(client_with_org: TestClient, name: str, asset_type: str = "model", **kwargs) -> dict:
    """Helper to create a test AI asset."""
    payload = {
        "name": name,
        "asset_type": asset_type,
        "business_criticality": kwargs.get("business_criticality", "critical"),
        "exposure_level": kwargs.get("exposure_level", "public"),
        "lifecycle_stage": kwargs.get("lifecycle_stage", "production"),
    }
    resp = client_with_org.post("/api/v1/inventory/assets", json=payload)
    assert resp.status_code == 201
    return resp.json()


def _create_test_policy(client_with_org: TestClient, name: str, rules: list, **kwargs) -> dict:
    """Helper to create a test governance policy."""
    payload = {
        "name": name,
        "policy_type": kwargs.get("policy_type", "deployment_gate"),
        "policy_definition": {"rules": rules},
        "enforcement_mode": kwargs.get("enforcement_mode", "enforce"),
        "description": kwargs.get("description", "Test policy"),
    }
    resp = client_with_org.post("/api/v1/policies", json=payload)
    assert resp.status_code == 201, f"Failed to create policy: {resp.text}"
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════
# Policy CRUD Tests
# ═══════════════════════════════════════════════════════════════════════

def test_create_policy(client_with_org: TestClient):
    """Test creating a governance policy."""
    resp = client_with_org.post("/api/v1/policies", json={
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


def test_create_policy_invalid_type(client_with_org: TestClient):
    """Test that invalid policy_type returns 400."""
    resp = client_with_org.post("/api/v1/policies", json={
        "name": "Bad Type",
        "policy_type": "nonexistent_type",
        "policy_definition": {"rules": []},
    })
    assert resp.status_code == 400


def test_create_policy_missing_rules(client_with_org: TestClient):
    """Test that policy_definition without 'rules' returns 400."""
    resp = client_with_org.post("/api/v1/policies", json={
        "name": "No Rules",
        "policy_type": "ai_usage",
        "policy_definition": {"something": "else"},
    })
    assert resp.status_code == 400


def test_list_policies(client_with_org: TestClient):
    """Test listing policies."""
    _create_test_policy(client_with_org, "Policy A", [])
    _create_test_policy(client_with_org, "Policy B", [])

    resp = client_with_org.get("/api/v1/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


def test_get_policy(client_with_org: TestClient):
    """Test getting a specific policy."""
    policy = _create_test_policy(client_with_org, "Get This Policy", [])

    resp = client_with_org.get(f"/api/v1/policies/{policy['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get This Policy"


def test_update_policy(client_with_org: TestClient):
    """Test updating a policy increments version."""
    policy = _create_test_policy(client_with_org, "Updatable Policy", [])
    assert policy["version"] == 1

    resp = client_with_org.patch(f"/api/v1/policies/{policy['id']}", json={
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

def test_evaluate_policy_pass(client_with_org: TestClient):
    """Test evaluating a policy that passes."""
    # Create an asset in development
    _create_test_asset(client_with_org, "Dev Model", asset_type="model", lifecycle_stage="development")

    # Create a policy that only triggers on production models
    policy = _create_test_policy(client_with_org, "Prod Only", [
        {
            "condition": "lifecycle_stage == 'production'",
            "require": "owner IS NOT NULL",
            "severity": "high",
        }
    ])

    resp = client_with_org.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "pass"
    assert len(data["violations"]) == 0


def test_evaluate_policy_fail_enforce(client_with_org: TestClient):
    """Test evaluating a policy in enforce mode that fails."""
    # Create a production model without an owner
    _create_test_asset(
        client_with_org, "Unowned Model", asset_type="model",
        lifecycle_stage="production",
    )

    # Policy requires owner for production models
    policy = _create_test_policy(client_with_org, "Owner Required", [
        {
            "condition": "lifecycle_stage == 'production'",
            "require": "owner IS NOT NULL",
            "severity": "critical",
        }
    ], enforcement_mode="enforce")

    resp = client_with_org.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "fail"
    assert len(data["violations"]) >= 1
    assert data["violations"][0]["severity"] == "critical"
    assert data["enforcement_mode"] == "enforce"


def test_evaluate_policy_warn_audit_mode(client_with_org: TestClient):
    """Test that violations in audit mode produce 'warn' instead of 'fail'."""
    _create_test_asset(
        client_with_org, "Audit Model", asset_type="model",
        lifecycle_stage="production",
    )

    policy = _create_test_policy(client_with_org, "Audit Only", [
        {
            "condition": "lifecycle_stage == 'production'",
            "require": "owner IS NOT NULL",
            "severity": "high",
        }
    ], enforcement_mode="audit")

    resp = client_with_org.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "warn"  # Not "fail" because mode is audit
    assert len(data["violations"]) >= 1


def test_evaluate_disabled_policy(client_with_org: TestClient):
    """Test that disabled policies always pass."""
    _create_test_asset(client_with_org, "Any Model", asset_type="model")

    policy = _create_test_policy(client_with_org, "Disabled Policy", [
        {
            "condition": "asset_type == 'model'",
            "require": "owner IS NOT NULL",
            "severity": "critical",
        }
    ], enforcement_mode="disabled")

    resp = client_with_org.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "pass"
    assert data["assets_evaluated"] == 0


def test_evaluate_all_policies(client_with_org: TestClient):
    """Test evaluating all active policies."""
    _create_test_asset(client_with_org, "All Eval Model", asset_type="model", lifecycle_stage="production")

    _create_test_policy(client_with_org, "Policy 1", [
        {"condition": "lifecycle_stage == 'production'", "require": "owner IS NOT NULL", "severity": "high"}
    ], enforcement_mode="enforce")
    _create_test_policy(client_with_org, "Policy 2", [], enforcement_mode="audit")

    resp = client_with_org.post("/api/v1/policies/evaluate-all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_policies"] >= 2
    assert "passing" in data
    assert "failing" in data
    assert "warning" in data


def test_policy_condition_in_operator(client_with_org: TestClient):
    """Test the IN operator in policy conditions."""
    _create_test_asset(client_with_org, "Agent Asset", asset_type="agent", lifecycle_stage="production")

    policy = _create_test_policy(client_with_org, "Type Gate", [
        {
            "condition": "asset_type IN ('agent', 'model')",
            "require": "business_criticality == 'critical'",
            "severity": "medium",
        }
    ])

    resp = client_with_org.post(f"/api/v1/policies/{policy['id']}/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    # Agent with critical criticality should pass
    assert data["result"] == "pass"


def test_policy_evaluation_history(client_with_org: TestClient):
    """Test that evaluations are recorded in the audit trail."""
    _create_test_asset(client_with_org, "Audited Model", asset_type="model")
    policy = _create_test_policy(client_with_org, "Audited Policy", [])

    # Evaluate twice
    client_with_org.post(f"/api/v1/policies/{policy['id']}/evaluate")
    client_with_org.post(f"/api/v1/policies/{policy['id']}/evaluate")

    resp = client_with_org.get(f"/api/v1/policies/{policy['id']}/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    for entry in data:
        assert entry["policy_id"] == policy["id"]
        assert "result" in entry
