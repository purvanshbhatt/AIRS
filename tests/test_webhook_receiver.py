"""
Webhook receiver tests — pushed payloads must be authenticated against the
org's webhook connector and persisted as telemetry events.
"""
import os

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

from app.models.telemetry_event import TelemetryEvent
from app.services.connector_manager import ConnectorManager

ORG_ID = "test-org-123"  # provisioned by the client_with_org fixture


def _register_webhook(db_session, secret="s3cr3t-shared"):
    mgr = ConnectorManager(db_session, ORG_ID)
    return mgr.register_connector(
        connector_type="webhook",
        display_name="MSP Feed",
        auth_method="webhook",
        credentials={"webhook_name": "MSP Feed", "webhook_secret": secret},
        config={"webhook_name": "MSP Feed", "webhook_secret": secret},
        created_by="test",
    )


def test_config_never_stores_secrets(db_session, client_with_org):
    connector = _register_webhook(db_session)
    assert "webhook_secret" not in (connector.config or {})
    resp = client_with_org.get(f"/api/v1/connectors?org_id={ORG_ID}")
    assert resp.status_code == 200
    item = resp.json()["connectors"][0]
    assert item["config"] == {"webhook_name": "MSP Feed"}


def test_webhook_rejects_missing_or_wrong_secret(db_session, client_with_org):
    _register_webhook(db_session)
    url = f"/api/v1/connectors/webhook/webhook?org_id={ORG_ID}"
    assert client_with_org.post(url, json={"event_type": "x"}).status_code == 401
    assert client_with_org.post(url, json={"event_type": "x"}, headers={"X-Webhook-Secret": "nope"}).status_code == 401


def test_webhook_unknown_org_is_404(db_session, client_with_org):
    resp = client_with_org.post(
        "/api/v1/connectors/webhook/webhook?org_id=nope", json={}, headers={"X-Webhook-Secret": "x"}
    )
    assert resp.status_code == 404


def test_webhook_ingests_payload_as_telemetry(db_session, client_with_org):
    connector = _register_webhook(db_session)
    url = f"/api/v1/connectors/webhook/webhook?org_id={ORG_ID}"
    payload = {"event_id": "evt-1", "event_type": "msp.backup_completed", "severity": "low", "job": "nightly"}
    resp = client_with_org.post(url, json=payload, headers={"X-Webhook-Secret": "s3cr3t-shared"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["events_ingested"] == 1

    # Idempotent on event_id
    resp2 = client_with_org.post(url, json=payload, headers={"X-Webhook-Secret": "s3cr3t-shared"})
    assert resp2.json()["events_ingested"] == 0

    rows = db_session.query(TelemetryEvent).filter(TelemetryEvent.org_id == ORG_ID).all()
    assert len(rows) == 1
    assert rows[0].event_type == "msp.backup_completed"
    assert rows[0].connector_id == connector.id

    db_session.refresh(connector)
    assert connector.status == "active"


def test_update_replaces_credentials_and_scrubs_config(db_session, client_with_org):
    connector = _register_webhook(db_session, secret="old")
    resp = client_with_org.patch(
        f"/api/v1/connectors/{connector.id}?org_id={ORG_ID}",
        json={"credentials": {"webhook_secret": "new"}, "config": {"webhook_name": "Renamed", "api_key": "leak"}},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["config"] == {"webhook_name": "Renamed"}
    url = f"/api/v1/connectors/webhook/webhook?org_id={ORG_ID}"
    assert client_with_org.post(url, json={"event_id": "e2"}, headers={"X-Webhook-Secret": "old"}).status_code == 401
    assert client_with_org.post(url, json={"event_id": "e2"}, headers={"X-Webhook-Secret": "new"}).status_code == 200
