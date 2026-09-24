# connectors.py

> 47 nodes · cohesion 0.11

## Key Concepts

- **connectors.py** (53 connections) — `app/api/v1/connectors.py`
- **_get_org_id()** (17 connections) — `app/api/v1/connectors.py`
- **ConnectorNotFoundError** (15 connections) — `app/services/connector_manager.py`
- **Session** (14 connections)
- **User** (13 connections)
- **connect_wazuh()** (12 connections) — `app/api/v1/connectors.py`
- **get_confidence()** (11 connections) — `app/api/v1/connectors.py`
- **check_microsoft_health()** (10 connections) — `app/api/v1/connectors.py`
- **trigger_microsoft_sync()** (10 connections) — `app/api/v1/connectors.py`
- **trigger_sync()** (10 connections) — `app/api/v1/connectors.py`
- **schemas/connector.py** (10 connections) — `app/schemas/connector.py`
- **check_health()** (9 connections) — `app/api/v1/connectors.py`
- **create_connector()** (9 connections) — `app/api/v1/connectors.py`
- **update_connector()** (9 connections) — `app/api/v1/connectors.py`
- **deactivate_connector()** (8 connections) — `app/api/v1/connectors.py`
- **get_connector()** (8 connections) — `app/api/v1/connectors.py`
- **get_sync_history()** (8 connections) — `app/api/v1/connectors.py`
- **list_connectors()** (8 connections) — `app/api/v1/connectors.py`
- **receive_webhook()** (7 connections) — `app/api/v1/connectors.py`
- **get** (6 connections)
- **ConnectorSyncResponse** (6 connections) — `app/schemas/connector.py`
- **post** (5 connections)
- **ConnectorCreateRequest** (5 connections) — `app/schemas/connector.py`
- **ConnectorHealthResponse** (5 connections) — `app/schemas/connector.py`
- **ConnectorListResponse** (5 connections) — `app/schemas/connector.py`
- *... and 22 more nodes in this community*

## Relationships

- [ConnectorManager](ConnectorManager.md) (15 shared connections)
- [User](User.md) (14 shared connections)
- [BaseModel](BaseModel.md) (10 shared connections)
- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [Entitlement](Entitlement.md) (6 shared connections)
- [WazuhConfig](WazuhConfig.md) (6 shared connections)
- [Connector](Connector.md) (6 shared connections)
- [api/integrations.py](api-integrations.py.md) (5 shared connections)
- [AdapterHealth](AdapterHealth.md) (4 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (3 shared connections)
- [test_evidence_integrity.py](test_evidence_integrity.py.md) (3 shared connections)
- [test_connectors_confidence_api.py](test_connectors_confidence_api.py.md) (2 shared connections)

## Source Files

- `app/api/v1/connectors.py`
- `app/schemas/connector.py`
- `app/schemas/evidence.py`
- `app/services/connector_manager.py`

## Audit Trail

- EXTRACTED: 158 (79%)
- INFERRED: 42 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*