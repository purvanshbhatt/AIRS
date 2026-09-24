# get_user_org_id

> 33 nodes · cohesion 0.10

## Key Concepts

- **get_user_org_id()** (26 connections) — `app/core/auth.py`
- **record_connector_audit()** (26 connections) — `app/services/audit.py`
- **check_splunk_logging_health()** (14 connections) — `app/api/v1/integrations.py`
- **configure_wazuh()** (14 connections) — `app/api/v1/integrations.py`
- **configure_splunk()** (13 connections) — `app/api/v1/integrations.py`
- **get_siem_integration_status()** (13 connections) — `app/api/v1/integrations.py`
- **get_wazuh_agent_status()** (11 connections) — `app/api/v1/integrations.py`
- **get_wazuh_vulnerabilities()** (11 connections) — `app/api/v1/integrations.py`
- **Session** (9 connections)
- **User** (9 connections)
- **configure_elastic()** (8 connections) — `app/api/v1/integrations.py`
- **trigger_sync()** (8 connections) — `app/api/v1/intelligence.py`
- **get_latest_versions()** (7 connections) — `app/api/v1/intelligence.py`
- **check_elastic_logging_health()** (6 connections) — `app/api/v1/integrations.py`
- **get** (5 connections)
- **post** (4 connections)
- **SyncResponse** (4 connections) — `app/api/v1/intelligence.py`
- **Session** (2 connections)
- **User** (2 connections)
- **HTTPException** (2 connections)
- **Session** (2 connections)
- **GET /api/integrations/wazuh/agent-status Fetches Wazuh agent connectivity…** (1 connections) — `app/api/v1/integrations.py`
- **GET /api/integrations/wazuh/vulnerabilities Fetches vulnerability alerts from…** (1 connections) — `app/api/v1/integrations.py`
- **POST /api/integrations/splunk/configure Requires: org_admin role Stores Splunk…** (1 connections) — `app/api/v1/integrations.py`
- **GET /api/integrations/splunk/logging-health Verifies that ResilAI logs are…** (1 connections) — `app/api/v1/integrations.py`
- *... and 8 more nodes in this community*

## Relationships

- [BaseModel](BaseModel.md) (20 shared connections)
- [User](User.md) (13 shared connections)
- [WazuhConfig](WazuhConfig.md) (13 shared connections)
- [api/integrations.py](api-integrations.py.md) (11 shared connections)
- [app/db/database.py](app-db-database.py.md) (10 shared connections)
- [Connector](Connector.md) (9 shared connections)
- [test_reliability.py](test_reliability.py.md) (2 shared connections)
- [connectors.py](connectors.py.md) (2 shared connections)
- [inventory.py](inventory.py.md) (2 shared connections)
- [policies.py](policies.py.md) (2 shared connections)
- [simulations.py](simulations.py.md) (2 shared connections)
- [telemetry_events.py](telemetry_events.py.md) (2 shared connections)

## Source Files

- `app/api/v1/integrations.py`
- `app/api/v1/intelligence.py`
- `app/core/auth.py`
- `app/services/audit.py`

## Audit Trail

- EXTRACTED: 118 (77%)
- INFERRED: 35 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*