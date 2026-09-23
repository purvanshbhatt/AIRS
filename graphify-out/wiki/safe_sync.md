# .safe_sync

> 6 nodes · cohesion 0.33

## Key Concepts

- **.safe_sync()** (5 connections) — `app/connectors/base.py`
- **.sync()** (5 connections) — `app/connectors/base.py`
- **.authenticate()** (3 connections) — `app/connectors/base.py`
- **Validate credentials and establish connection. Returns True on success.** (1 connections) — `app/connectors/base.py`
- **Fetch and normalize telemetry events from the source. Returns normalized events.** (1 connections) — `app/connectors/base.py`
- **Sync with error handling, timing, and logging.** (1 connections) — `app/connectors/base.py`

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (4 shared connections)
- [Connector](Connector.md) (1 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (1 shared connections)

## Source Files

- `app/connectors/base.py`

## Audit Trail

- EXTRACTED: 11 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*