# test_microsoft_connector.py

> 49 nodes · cohesion 0.06

## Key Concepts

- **test_microsoft_connector.py** (33 connections) — `tests/test_microsoft_connector.py`
- **request_with_backoff()** (9 connections) — `app/connectors/microsoft.py`
- **test_connector_sync_normalization()** (9 connections) — `tests/test_microsoft_connector.py`
- **schemas/microsoft.py** (7 connections) — `app/schemas/microsoft.py`
- **DefenderAlertTelemetry** (7 connections) — `app/schemas/microsoft.py`
- **EntraUserTelemetry** (7 connections) — `app/schemas/microsoft.py`
- **IntuneDeviceTelemetry** (7 connections) — `app/schemas/microsoft.py`
- **TelemetryPayload** (7 connections) — `app/schemas/microsoft.py`
- **DefenderService** (5 connections) — `app/connectors/microsoft.py`
- **EntraIDService** (5 connections) — `app/connectors/microsoft.py`
- **IntuneService** (5 connections) — `app/connectors/microsoft.py`
- **asyncio** (5 connections)
- **test_authenticate_failure()** (5 connections) — `tests/test_microsoft_connector.py`
- **test_authenticate_success()** (5 connections) — `tests/test_microsoft_connector.py`
- **test_request_with_backoff_429()** (5 connections) — `tests/test_microsoft_connector.py`
- **test_verification_service_evaluation()** (5 connections) — `tests/test_microsoft_connector.py`
- **.fetch_alerts()** (4 connections) — `app/connectors/microsoft.py`
- **.fetch_users_and_mfa()** (4 connections) — `app/connectors/microsoft.py`
- **.fetch_devices()** (4 connections) — `app/connectors/microsoft.py`
- **AsyncClient** (4 connections)
- **patch** (4 connections)
- **MockFinding** (3 connections) — `tests/test_microsoft_connector.py`
- **test_api_routes_not_found()** (3 connections) — `tests/test_microsoft_connector.py`
- **test_connector_initialization()** (3 connections) — `tests/test_microsoft_connector.py`
- **.__init__()** (2 connections) — `app/connectors/microsoft.py`
- *... and 24 more nodes in this community*

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (15 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (9 shared connections)
- [BaseModel](BaseModel.md) (4 shared connections)
- [Connector](Connector.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [VerificationService](VerificationService.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [api/integrations.py](api-integrations.py.md) (1 shared connections)
- [main.py](main.py.md) (1 shared connections)
- [schemas/verification.py](schemas-verification.py.md) (1 shared connections)
- [test_connector_registration](test_connector_registration.md) (1 shared connections)

## Source Files

- `app/connectors/microsoft.py`
- `app/schemas/microsoft.py`
- `tests/test_microsoft_connector.py`

## Audit Trail

- EXTRACTED: 109 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*