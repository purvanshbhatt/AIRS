# SplunkAdapter

> 23 nodes · cohesion 0.12

## Key Concepts

- **SplunkAdapter** (21 connections) — `app/services/evidence/adapters/splunk.py`
- **test_splunk_adapter.py** (13 connections) — `tests/test_splunk_adapter.py`
- **.fetch_evidence()** (4 connections) — `app/services/evidence/adapters/splunk.py`
- **asyncio** (4 connections)
- **.health()** (3 connections) — `app/services/evidence/adapters/splunk.py`
- **splunk_adapter()** (3 connections) — `tests/test_splunk_adapter.py`
- **splunk_connector()** (3 connections) — `tests/test_splunk_adapter.py`
- **test_splunk_adapter_health_ok()** (3 connections) — `tests/test_splunk_adapter.py`
- **test_splunk_adapter_health_raises()** (3 connections) — `tests/test_splunk_adapter.py`
- **test_splunk_adapter_health_unhealthy()** (3 connections) — `tests/test_splunk_adapter.py`
- **test_splunk_adapter_no_connector_returns_failure()** (3 connections) — `tests/test_splunk_adapter.py`
- **datetime** (2 connections)
- **.bind_connector()** (2 connections) — `app/services/evidence/adapters/splunk.py`
- **fixture** (2 connections)
- **test_splunk_adapter_conformance()** (2 connections) — `tests/test_splunk_adapter.py`
- **EvidenceAdapter** (1 connections)
- **EvidenceAdapter implementation for Splunk. The adapter delegates to a…** (1 connections) — `app/services/evidence/adapters/splunk.py`
- **Bind the SplunkConnector that owns this adapter's telemetry.** (1 connections) — `app/services/evidence/adapters/splunk.py`
- **Fetch all evidence checks from Splunk. This is a thin shim — production code…** (1 connections) — `app/services/evidence/adapters/splunk.py`
- **Report live adapter health via the bound SplunkConnector. Returns a clean…** (1 connections) — `app/services/evidence/adapters/splunk.py`
- **.connector_name()** (1 connections) — `app/services/evidence/adapters/splunk.py`
- **.__init__()** (1 connections) — `app/services/evidence/adapters/splunk.py`
- **A ``MagicMock`` shaped like SplunkConnector for unit tests.** (1 connections) — `tests/test_splunk_adapter.py`

## Relationships

- [EvidenceAdapter](EvidenceAdapter.md) (8 shared connections)
- [EvidenceRecord](EvidenceRecord.md) (4 shared connections)
- [AdapterHealth](AdapterHealth.md) (4 shared connections)
- [ConnectorManager](ConnectorManager.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `app/services/evidence/adapters/splunk.py`
- `tests/test_splunk_adapter.py`

## Audit Trail

- EXTRACTED: 44 (90%)
- INFERRED: 5 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*