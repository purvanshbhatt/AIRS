# VeeamConnector

> 12 nodes · cohesion 0.20

## Key Concepts

- **VeeamConnector** (14 connections) — `app/connectors/veeam.py`
- **.authenticate()** (4 connections) — `app/connectors/veeam.py`
- **.sync()** (4 connections) — `app/connectors/veeam.py`
- **.validate_permissions()** (4 connections) — `app/connectors/veeam.py`
- **.health_check()** (3 connections) — `app/connectors/veeam.py`
- **Connector** (1 connections)
- **Probe Veeam REST API reachability.** (1 connections) — `app/connectors/veeam.py`
- **Validate read permissions on jobs endpoint.** (1 connections) — `app/connectors/veeam.py`
- **Veeam Backup & Replication REST API telemetry connector. Credentials: -…** (1 connections) — `app/connectors/veeam.py`
- **Verify API token against Veeam REST API.** (1 connections) — `app/connectors/veeam.py`
- **Fetch backup jobs from Veeam and normalize into events.** (1 connections) — `app/connectors/veeam.py`
- **.__init__()** (1 connections) — `app/connectors/veeam.py`

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (8 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (2 shared connections)

## Source Files

- `app/connectors/veeam.py`

## Audit Trail

- EXTRACTED: 18 (78%)
- INFERRED: 5 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*