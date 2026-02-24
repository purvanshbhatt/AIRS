import json
from app.models.organization import Organization
from app.models.webhook import Webhook
from app.services.integrations import dispatch_assessment_scored_webhooks


def _submit_full_answers(client, assessment_id: str):
    answers = [
        {"question_id": "tl_01", "value": "true"},
        {"question_id": "tl_02", "value": "true"},
        {"question_id": "tl_03", "value": "true"},
        {"question_id": "tl_04", "value": "true"},
        {"question_id": "tl_05", "value": "90"},
        {"question_id": "tl_06", "value": "true"},
        {"question_id": "dc_01", "value": "85"},
        {"question_id": "dc_02", "value": "true"},
        {"question_id": "dc_03", "value": "true"},
        {"question_id": "dc_04", "value": "true"},
        {"question_id": "dc_05", "value": "true"},
        {"question_id": "dc_06", "value": "true"},
        {"question_id": "iv_01", "value": "true"},
        {"question_id": "iv_02", "value": "true"},
        {"question_id": "iv_03", "value": "true"},
        {"question_id": "iv_04", "value": "true"},
        {"question_id": "iv_05", "value": "true"},
        {"question_id": "iv_06", "value": "true"},
        {"question_id": "ir_01", "value": "true"},
        {"question_id": "ir_02", "value": "true"},
        {"question_id": "ir_03", "value": "true"},
        {"question_id": "ir_04", "value": "true"},
        {"question_id": "ir_05", "value": "true"},
        {"question_id": "ir_06", "value": "true"},
        {"question_id": "rs_01", "value": "true"},
        {"question_id": "rs_02", "value": "true"},
        {"question_id": "rs_03", "value": "true"},
        {"question_id": "rs_04", "value": "true"},
        {"question_id": "rs_05", "value": "4"},
        {"question_id": "rs_06", "value": "true"},
    ]
    response = client.post(f"/api/assessments/{assessment_id}/answers", json={"answers": answers})
    assert response.status_code == 200


def _create_scored_assessment(client):
    org_resp = client.post("/api/orgs", json={"name": "Integrations Org"})
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    assessment_resp = client.post("/api/assessments", json={"organization_id": org_id, "title": "Integration Test"})
    assert assessment_resp.status_code == 201
    assessment_id = assessment_resp.json()["id"]

    _submit_full_answers(client, assessment_id)
    score_resp = client.post(f"/api/assessments/{assessment_id}/score")
    assert score_resp.status_code == 200

    return org_id, assessment_id


def test_external_latest_score_requires_api_key(client):
    _create_scored_assessment(client)

    response = client.get("/api/external/latest-score")
    assert response.status_code == 401


def test_external_latest_score_with_valid_api_key(client):
    org_id, assessment_id = _create_scored_assessment(client)

    key_resp = client.post(f"/api/orgs/{org_id}/api-keys", json={"scopes": ["scores:read"]})
    assert key_resp.status_code == 201
    plaintext_key = key_resp.json()["api_key"]

    response = client.get(
        "/api/external/latest-score",
        headers={"X-AIRS-API-Key": plaintext_key},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["org_id"] == org_id
    assert data["assessment_id"] == assessment_id
    assert "overall_score" in data
    assert "risk_summary" in data
    assert "top_findings" in data


def test_external_latest_score_rejects_insufficient_scope(client):
    org_id, _ = _create_scored_assessment(client)

    key_resp = client.post(f"/api/orgs/{org_id}/api-keys", json={"scopes": ["webhooks:write"]})
    assert key_resp.status_code == 201
    plaintext_key = key_resp.json()["api_key"]

    response = client.get(
        "/api/external/latest-score",
        headers={"X-AIRS-API-Key": plaintext_key},
    )
    assert response.status_code == 403


def test_compute_score_enqueues_webhook_dispatch(client, monkeypatch):
    org_resp = client.post("/api/orgs", json={"name": "Webhook Org"})
    org_id = org_resp.json()["id"]

    assessment_resp = client.post("/api/assessments", json={"organization_id": org_id, "title": "Webhook Trigger"})
    assessment_id = assessment_resp.json()["id"]

    _submit_full_answers(client, assessment_id)

    calls = []

    def _fake_dispatch(org_id_arg, payload_arg):
        calls.append((org_id_arg, payload_arg))

    monkeypatch.setattr("app.api.assessments.dispatch_assessment_scored_webhooks", _fake_dispatch)

    response = client.post(f"/api/assessments/{assessment_id}/score")
    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0][0] == org_id
    assert calls[0][1]["event_type"] == "assessment.scored"


def test_dispatch_assessment_scored_webhooks_retries(db_session, monkeypatch):
    org = Organization(name="Retry Org", owner_uid="dev-user")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    hook = Webhook(
        org_id=org.id,
        url="https://example.com/webhook",
        event_types=json.dumps(["assessment.scored"]),
        secret=None,
        is_active=True,
    )
    db_session.add(hook)
    db_session.commit()

    attempts = {"count": 0}

    def _fake_deliver(_hook, _event_type, _payload):
        attempts["count"] += 1
        if attempts["count"] < 3:
            return False, 500, "temporary"
        return True, 200, None

    monkeypatch.setattr("app.services.integrations.deliver_webhook", _fake_deliver)
    monkeypatch.setattr("app.services.integrations.SessionLocal", lambda: db_session)

    dispatch_assessment_scored_webhooks(
        org.id,
        {
            "event_type": "assessment.scored",
            "org_id": org.id,
            "assessment_id": "a-1",
            "score": 81.0,
            "critical_findings": 0,
            "generated_at": "2026-02-14T00:00:00Z",
        },
    )

    assert attempts["count"] == 3


def test_mock_splunk_seed_and_list_external_findings(client):
    org_resp = client.post("/api/orgs", json={"name": "Splunk Demo Org"})
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    seed_resp = client.post("/api/integrations/mock/splunk-seed", json={"org_id": org_id})
    assert seed_resp.status_code == 200
    seed_data = seed_resp.json()
    assert seed_data["org_id"] == org_id
    assert seed_data["source"] == "splunk"
    assert seed_data["inserted"] == 10
    assert seed_data["connected"] is True

    list_resp = client.get(f"/api/integrations/external-findings?source=splunk&limit=50&org_id={org_id}")
    assert list_resp.status_code == 200
    findings = list_resp.json()
    assert len(findings) == 10
    assert findings[0]["source"] == "splunk"
    assert "raw_json" in findings[0]


def test_webhook_url_test_endpoint_sends_payload(client, monkeypatch):
    calls = []

    def _fake_url_test(url, event_type, payload, secret=None):
        calls.append(
            {
                "url": url,
                "event_type": event_type,
                "payload": payload,
                "secret": secret,
            }
        )
        return True, 202, None

    monkeypatch.setattr("app.api.integrations.deliver_webhook_url_test", _fake_url_test)

    resp = client.post(
        "/api/integrations/webhooks/test",
        json={
            "url": "https://example.com/webhook",
            "event_type": "assessment.scored.test",
            "secret": "test-secret",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["delivered"] is True
    assert data["status_code"] == 202
    assert data["event_type"] == "assessment.scored.test"
    assert data["payload"]["event_type"] == "assessment.scored.test"
    assert data["payload"]["assessment_id"] == "test-assessment"

    assert len(calls) == 1
    assert calls[0]["url"] == "https://example.com/webhook"
    assert calls[0]["event_type"] == "assessment.scored.test"
    assert calls[0]["secret"] == "test-secret"


def test_org_audit_endpoint_records_core_events(client, monkeypatch):
    org_resp = client.post("/api/orgs", json={"name": "Audit Org"})
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    assessment_resp = client.post("/api/assessments", json={"organization_id": org_id, "title": "Audit Assessment"})
    assert assessment_resp.status_code == 201
    assessment_id = assessment_resp.json()["id"]

    _submit_full_answers(client, assessment_id)
    score_resp = client.post(f"/api/assessments/{assessment_id}/score")
    assert score_resp.status_code == 200

    key_resp = client.post(f"/api/orgs/{org_id}/api-keys", json={"scopes": ["scores:read"]})
    assert key_resp.status_code == 201

    webhook_resp = client.post(
        f"/api/orgs/{org_id}/webhooks",
        json={"url": "https://example.com/hook", "event_types": ["assessment.scored"]},
    )
    assert webhook_resp.status_code == 201
    webhook_id = webhook_resp.json()["id"]

    monkeypatch.setattr("app.api.integrations.deliver_webhook", lambda *_args, **_kwargs: (True, 200, None))
    test_resp = client.post(f"/api/webhooks/{webhook_id}/test")
    assert test_resp.status_code == 200

    audit_resp = client.get(f"/api/orgs/{org_id}/audit")
    assert audit_resp.status_code == 200
    actions = {item["action"] for item in audit_resp.json()}
    assert "assessment.created" in actions
    assert "assessment.score_generated" in actions
    assert "api_key.created" in actions
    assert "webhook.triggered.manual_test" in actions
