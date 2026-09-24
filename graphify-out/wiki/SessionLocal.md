# SessionLocal

> 26 nodes · cohesion 0.08

## Key Concepts

- **SessionLocal** (29 connections)
- **TaskScheduler** (10 connections) — `app/tasks/scheduler.py`
- **websocket_telemetry_endpoint()** (5 connections) — `app/main.py`
- **setup_db()** (5 connections) — `tests/test_runtime_guardrails.py`
- **._monitor_health()** (4 connections) — `app/tasks/scheduler.py`
- **._run_periodic()** (4 connections) — `app/tasks/scheduler.py`
- **._sync_connectors()** (4 connections) — `app/tasks/scheduler.py`
- **test_db()** (4 connections) — `tests/test_demo_isolation.py`
- **test_db()** (4 connections) — `tests/test_tenant_isolation_v2.py`
- **.start()** (3 connections) — `app/tasks/scheduler.py`
- **.stop()** (2 connections) — `app/tasks/scheduler.py`
- **run_resilience()** (2 connections) — `phase3_resilience.py`
- **websocket** (1 connections)
- **WebSocket connection that registers clients for real-time, event-driven GHI…** (1 connections) — `app/main.py`
- **Any** (1 connections)
- **Check the health of active connectors periodically.** (1 connections) — `app/tasks/scheduler.py`
- **Start the background task scheduler.** (1 connections) — `app/tasks/scheduler.py`
- **Stop all background tasks.** (1 connections) — `app/tasks/scheduler.py`
- **Run a coroutine periodically.** (1 connections) — `app/tasks/scheduler.py`
- **Trigger syncs for active connectors. (Implementation matches Phase 1 stub…** (1 connections) — `app/tasks/scheduler.py`
- **.__init__()** (1 connections) — `app/tasks/scheduler.py`
- **fixture** (1 connections)
- **Create an isolated in-memory SQLite database for testing.** (1 connections) — `tests/test_demo_isolation.py`
- **fixture** (1 connections)
- **fixture** (1 connections)
- *... and 1 more nodes in this community*

## Relationships

- [Organization](Organization.md) (7 shared connections)
- [Connector](Connector.md) (4 shared connections)
- [splunk_staging_validation.py](splunk_staging_validation.py.md) (4 shared connections)
- [ConnectorManager](ConnectorManager.md) (3 shared connections)
- [router.py](router.py.md) (2 shared connections)
- [test_connector_progress.py](test_connector_progress.py.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [WazuhConfig](WazuhConfig.md) (2 shared connections)
- [User](User.md) (2 shared connections)
- [main.py](main.py.md) (1 shared connections)
- [get_firestore_client](get_firestore_client.md) (1 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)

## Source Files

- `app/main.py`
- `app/tasks/scheduler.py`
- `phase3_resilience.py`
- `tests/test_demo_isolation.py`
- `tests/test_runtime_guardrails.py`
- `tests/test_tenant_isolation_v2.py`

## Audit Trail

- EXTRACTED: 30 (48%)
- INFERRED: 33 (52%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*