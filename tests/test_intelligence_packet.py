from unittest.mock import patch


def _valid_packet():
    return {
        "simulation": {
            "scenario_name": "The Ghost Protocol",
            "threat_vector": "Prompt Injection",
            "mapped_frameworks": ["EU AI Act Art. 14", "NIST PR.DS-1"],
            "attack_flow": [
                "Adversary injects hidden instruction into retrieval source",
                "Model follows malicious override",
                "Unauthorized action is attempted",
            ],
            "impact_analysis": {
                "financial_risk": "$150K-300K",
                "operational_downtime": "2-4 hours",
                "data_integrity_score": 62,
            },
        },
        "remediation_ledger": [
            {
                "task_id": "R-001",
                "action": "Enable Firestore field-level encryption",
                "priority": "Critical",
                "ghi_impact": 8.5,
                "automation_potential": True,
            },
            {
                "task_id": "R-002",
                "action": "Block external domain redirects in RAG responses",
                "priority": "High",
                "ghi_impact": 4.0,
                "automation_potential": True,
            },
        ],
    }


def _create_org(client):
    response = client.post(
        "/api/orgs",
        json={
            "name": "Test Org",
            "industry": "Technology",
            "size": "201-1000",
            "contact_email": "owner@example.com",
            "notes": "created for tests",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_ingest_intelligence_packet_success(client):
    org_id = _create_org(client)

    with patch("app.api.intelligence.firestore_upsert_remediation_ledger") as upsert_mock:
        upsert_mock.return_value = {
            "tasks_upserted": 2,
            "ledger_collection_path": (
                f"organizations/{org_id}/workspaces/ws-1/audits/audit-1/remediation_ledger"
            ),
        }

        response = client.post(
            f"/api/orgs/{org_id}/workspaces/ws-1/audits/audit-1/intelligence-packet",
            json=_valid_packet(),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["tasks_upserted"] == 2
    assert payload["org_id"] == org_id
    upsert_mock.assert_called_once()


def test_ingest_intelligence_packet_rejects_invalid_contract(client):
    org_id = _create_org(client)
    bad = _valid_packet()
    bad["simulation"]["impact_analysis"]["data_integrity_score"] = 101
    bad["simulation"]["unexpected"] = "break-contract"

    response = client.post(
        f"/api/orgs/{org_id}/workspaces/ws-1/audits/audit-1/intelligence-packet",
        json=bad,
    )

    assert response.status_code == 422
