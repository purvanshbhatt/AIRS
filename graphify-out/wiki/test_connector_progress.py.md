# test_connector_progress.py

> 33 nodes · cohesion 0.10

## Key Concepts

- **test_connector_progress.py** (15 connections) — `tests/test_connector_progress.py`
- **TelemetryConnectionManager** (14 connections) — `app/core/websocket_manager.py`
- **run_wazuh_connect_sync()** (12 connections) — `app/services/wazuh_client.py`
- **ConnectorProgressEvent** (8 connections) — `app/schemas/connector_progress.py`
- **ConnectorProgressState** (8 connections) — `app/schemas/connector_progress.py`
- **.broadcast_org_update()** (6 connections) — `app/core/websocket_manager.py`
- **.broadcast_connector_progress()** (5 connections) — `app/core/websocket_manager.py`
- **connector_progress.py** (5 connections) — `app/schemas/connector_progress.py`
- **patch** (5 connections)
- **test_run_wazuh_connect_sync_failure()** (5 connections) — `tests/test_connector_progress.py`
- **test_run_wazuh_connect_sync_success()** (5 connections) — `tests/test_connector_progress.py`
- **.disconnect()** (4 connections) — `app/core/websocket_manager.py`
- **mock_auth()** (4 connections) — `tests/test_connector_progress.py`
- **test_progress_event_model()** (4 connections) — `tests/test_connector_progress.py`
- **mock_db_session()** (3 connections) — `tests/test_connector_progress.py`
- **fixture** (3 connections)
- **test_configure_wazuh_endpoint_initiates_background_sync()** (3 connections) — `tests/test_connector_progress.py`
- **WebSocket** (2 connections)
- **.connect()** (2 connections) — `app/core/websocket_manager.py`
- **Enum** (2 connections)
- **asyncio** (2 connections)
- **setup_db()** (2 connections) — `tests/test_connector_progress.py`
- **Broadcasts a connector progress event to all connected clients for the…** (1 connections) — `app/core/websocket_manager.py`
- **Fetches the latest GHI and connector health for the org and broadcasts it to…** (1 connections) — `app/core/websocket_manager.py`
- **.__init__()** (1 connections) — `app/core/websocket_manager.py`
- *... and 8 more nodes in this community*

## Relationships

- [WazuhConfig](WazuhConfig.md) (7 shared connections)
- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [api/integrations.py](api-integrations.py.md) (3 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (2 shared connections)
- [SessionLocal](SessionLocal.md) (2 shared connections)
- [User](User.md) (2 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)
- [_make_org](_make_org.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)
- [get_user_org_id](get_user_org_id.md) (1 shared connections)
- [main.py](main.py.md) (1 shared connections)

## Source Files

- `app/core/websocket_manager.py`
- `app/schemas/connector_progress.py`
- `app/services/wazuh_client.py`
- `tests/test_connector_progress.py`

## Audit Trail

- EXTRACTED: 64 (82%)
- INFERRED: 14 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*