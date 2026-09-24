# api/integrations.py

> 41 nodes · cohesion 0.12

## Key Concepts

- **api/integrations.py** (70 connections) — `app/api/integrations.py`
- **ConnectorType** (35 connections) — `app/models/connector.py`
- **User** (18 connections)
- **Session** (17 connections)
- **configure_wazuh()** (16 connections) — `app/api/integrations.py`
- **refresh_wazuh_cache()** (15 connections) — `app/services/wazuh_client.py`
- **configure_splunk_hec()** (13 connections) — `app/api/integrations.py`
- **pull_splunk_evidence()** (12 connections) — `app/api/integrations.py`
- **get_wazuh_agent_status()** (10 connections) — `app/api/integrations.py`
- **get_wazuh_vulnerabilities()** (10 connections) — `app/api/integrations.py`
- **firestore_save_wazuh_config()** (10 connections) — `app/db/firestore.py`
- **create_api_key()** (9 connections) — `app/api/integrations.py`
- **get_integration_status()** (9 connections) — `app/api/integrations.py`
- **create_webhook()** (8 connections) — `app/api/integrations.py`
- **get_splunk_config()** (8 connections) — `app/api/integrations.py`
- **post** (8 connections)
- **test_webhook()** (8 connections) — `app/api/integrations.py`
- **get** (7 connections)
- **remove_splunk_config()** (7 connections) — `app/api/integrations.py`
- **seed_mock_splunk_findings()** (7 connections) — `app/api/integrations.py`
- **delete_api_key()** (6 connections) — `app/api/integrations.py`
- **delete_webhook()** (6 connections) — `app/api/integrations.py`
- **list_api_keys()** (6 connections) — `app/api/integrations.py`
- **list_external_findings()** (6 connections) — `app/api/integrations.py`
- **list_webhooks()** (6 connections) — `app/api/integrations.py`
- *... and 16 more nodes in this community*

## Relationships

- [BaseModel](BaseModel.md) (28 shared connections)
- [User](User.md) (22 shared connections)
- [Connector](Connector.md) (20 shared connections)
- [WazuhConfig](WazuhConfig.md) (20 shared connections)
- [services/integrations.py](services-integrations.py.md) (15 shared connections)
- [app/db/database.py](app-db-database.py.md) (14 shared connections)
- [get_user_org_id](get_user_org_id.md) (11 shared connections)
- [Entitlement](Entitlement.md) (8 shared connections)
- [connectors.py](connectors.py.md) (5 shared connections)
- [test_connector_progress.py](test_connector_progress.py.md) (3 shared connections)
- [get_firestore_client](get_firestore_client.md) (3 shared connections)
- [ConnectorManager](ConnectorManager.md) (2 shared connections)

## Source Files

- `app/api/integrations.py`
- `app/db/firestore.py`
- `app/models/connector.py`
- `app/schemas/integrations.py`
- `app/services/wazuh_client.py`

## Audit Trail

- EXTRACTED: 192 (75%)
- INFERRED: 65 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*