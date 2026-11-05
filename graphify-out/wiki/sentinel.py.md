# sentinel.py

> 14 nodes · cohesion 0.26

## Key Concepts

- **sentinel.py** (33 connections) — `app/api/routes/sentinel.py`
- **trigger_splunk_sync()** (8 connections) — `app/api/routes/sentinel.py`
- **Session** (7 connections)
- **get** (5 connections)
- **get_board_report()** (4 connections) — `app/api/routes/sentinel.py`
- **get_telemetry()** (4 connections) — `app/api/routes/sentinel.py`
- **run_digital_twin_simulation()** (4 connections) — `app/api/routes/sentinel.py`
- **get_evidence()** (3 connections) — `app/api/routes/sentinel.py`
- **get_sentinel_status()** (3 connections) — `app/api/routes/sentinel.py`
- **list_simulations()** (3 connections) — `app/api/routes/sentinel.py`
- **get_current_org()** (2 connections) — `app/api/routes/sentinel.py`
- **post** (2 connections)
- **BackgroundTasks** (1 connections)
- **Mock auth for the hackathon demo.** (1 connections) — `app/api/routes/sentinel.py`

## Relationships

- [splunk_staging_validation.py](splunk_staging_validation.py.md) (9 shared connections)
- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [Connector](Connector.md) (4 shared connections)
- [twin/engine.py](twin-engine.py.md) (3 shared connections)
- [middleware.py](middleware.py.md) (2 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (2 shared connections)
- [api/integrations.py](api-integrations.py.md) (2 shared connections)
- [ConnectorManager](ConnectorManager.md) (2 shared connections)
- [TelemetryEvidence](TelemetryEvidence.md) (1 shared connections)
- [SplunkConnector](SplunkConnector.md) (1 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `app/api/routes/sentinel.py`

## Audit Trail

- EXTRACTED: 52 (93%)
- INFERRED: 4 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*