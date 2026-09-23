# SplunkConnector

> 16 nodes · cohesion 0.25

## Key Concepts

- **SplunkConnector** (27 connections) — `app/connectors/splunk.py`
- **._run_search()** (7 connections) — `app/connectors/splunk.py`
- **.sync()** (7 connections) — `app/connectors/splunk.py`
- **RawEvent** (6 connections)
- **._sync_edr()** (4 connections) — `app/connectors/splunk.py`
- **._sync_logging_health()** (4 connections) — `app/connectors/splunk.py`
- **._sync_mfa()** (4 connections) — `app/connectors/splunk.py`
- **._sync_notable()** (4 connections) — `app/connectors/splunk.py`
- **.validate_permissions()** (3 connections) — `app/connectors/splunk.py`
- **.authenticate()** (2 connections) — `app/connectors/splunk.py`
- **.health_check()** (2 connections) — `app/connectors/splunk.py`
- **.__init__()** (2 connections) — `app/connectors/splunk.py`
- **._map_severity()** (2 connections) — `app/connectors/splunk.py`
- **Connector** (1 connections)
- **Fetch priority security telemetry via Splunk MCP.** (1 connections) — `app/connectors/splunk.py`
- **Splunk SIEM connector backed by the Splunk MCP Server. Pulls four canonical…** (1 connections) — `app/connectors/splunk.py`

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (9 shared connections)
- [SplunkMCPClient](SplunkMCPClient.md) (3 shared connections)
- [sentinel.py](sentinel.py.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)
- [EvidenceAdapter](EvidenceAdapter.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (1 shared connections)

## Source Files

- `app/connectors/splunk.py`

## Audit Trail

- EXTRACTED: 40 (85%)
- INFERRED: 7 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*