"""
Tests for 48-Hour Live AI Agent Blast-Radius Audit lifecycle and endpoints.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.organization import Organization
from app.models.agent_audit import AgentAudit


@pytest.fixture
def test_org(db_session):
    org_id = f"test-org-{int(datetime.now(timezone.utc).timestamp())}"
    org = Organization(
        id=org_id,
        name="Test Audit Organization",
        subscription_plan="design-partner",
        subscription_status="active",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def unpaid_org(db_session):
    org_id = f"unpaid-org-{int(datetime.now(timezone.utc).timestamp())}"
    org = Organization(
        id=org_id,
        name="Unpaid Organization",
        subscription_plan="free",
        subscription_status="unpaid",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


def test_demo_agent_audit_list(client):
    """Demo organizations receive mock demo audit data."""
    res = client.get("/api/orgs/demo-health-org/agent-audits")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["id"] == "audit-demo-48h"
    assert data[0]["readiness_score"] == 60.0


def test_demo_agent_audit_get(client):
    """Fetching single demo audit returns mock demo audit."""
    res = client.get("/api/orgs/demo-health-org/agent-audits/audit-demo-48h")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "audit-demo-48h"
    assert len(data["findings"]) == 3


def test_create_agent_audit_paywall(client, unpaid_org):
    """Unpaid real organization cannot create agent audit without subscription (HTTP 402)."""
    res = client.post(
        f"/api/orgs/{unpaid_org.id}/agent-audits",
        json={"audit_window": "48h", "source_type": "splunk"},
    )
    assert res.status_code == 402
    assert "subscription" in res.json()["error"]["message"].lower()


def test_create_and_run_agent_audit_lifecycle(client, test_org):
    """Entitled organization can create, ingest telemetry, and run 48-hour blast-radius audit."""
    # 1. Create session
    create_res = client.post(
        f"/api/orgs/{test_org.id}/agent-audits",
        json={
            "audit_window": "48h",
            "source_type": "agent_trace",
            "agent_name": "Triage AI Bot",
            "environment": "Production",
        },
    )
    assert create_res.status_code == 200
    audit = create_res.json()
    audit_id = audit["id"]
    assert audit["status"] == "CREATED"
    assert audit["audit_window"] == "48h"

    # Verify 48-hour time-bound
    created_at = datetime.fromisoformat(audit["created_at"])
    expires_at = datetime.fromisoformat(audit["expires_at"])
    duration_hours = (expires_at - created_at).total_seconds() / 3600
    assert abs(duration_hours - 48.0) < 0.1

    # 2. Ingest telemetry
    telemetry_events = [
        {"agent_id": "Triage AI Bot", "tool": "bash_shell", "action": "exec", "params": {"cmd": "ls -la"}},
        {"agent_id": "Triage AI Bot", "tool": "patient_lookup", "action": "read", "authorized": True},
    ]
    ingest_res = client.post(
        f"/api/orgs/{test_org.id}/agent-audits/{audit_id}/telemetry",
        json={"events": telemetry_events},
    )
    assert ingest_res.status_code == 200
    assert ingest_res.json()["ingested_events"] == 2

    # 3. Run deterministic analysis
    run_res = client.post(f"/api/orgs/{test_org.id}/agent-audits/{audit_id}/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] == "COMPLETE"
    assert run_data["readiness_score"] == 60.0  # 100 - (20 + 15 + 5)
    assert len(run_data["findings"]) == 3
    assert "NIST AI RMF" in run_data["framework_alignment"]

    # 4. Narrative Explanation
    exp_res = client.get(f"/api/orgs/{test_org.id}/agent-audits/{audit_id}/explanation")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert "explanation" in exp_data
    assert len(exp_data["explanation"]) > 20

    # 5. PDF Report download
    rep_res = client.get(f"/api/orgs/{test_org.id}/agent-audits/{audit_id}/report")
    assert rep_res.status_code == 200
    assert rep_res.headers.get("content-type") == "application/pdf"
    assert len(rep_res.content) > 50


def test_expired_audit_cannot_ingest_or_run(client, test_org, db_session):
    """An audit session past its 48-hour observation window cannot ingest new events."""
    past = datetime.now(timezone.utc) - timedelta(hours=50)
    audit = AgentAudit(
        id=f"audit_expired_test",
        org_id=test_org.id,
        created_at=past,
        expires_at=past + timedelta(hours=48),
        status="INGESTING",
    )
    db_session.add(audit)
    db_session.commit()

    res = client.post(
        f"/api/orgs/{test_org.id}/agent-audits/{audit.id}/telemetry",
        json={"events": [{"test": 1}]},
    )
    assert res.status_code == 400
    err_msg = res.json().get("error", {}).get("message", "") or res.json().get("detail", "")
    assert "expired" in err_msg.lower()
