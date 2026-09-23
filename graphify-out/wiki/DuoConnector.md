# DuoConnector

> 15 nodes · cohesion 0.17

## Key Concepts

- **DuoConnector** (15 connections) — `app/connectors/duo.py`
- **.authenticate()** (5 connections) — `app/connectors/duo.py`
- **._sign()** (5 connections) — `app/connectors/duo.py`
- **.sync()** (5 connections) — `app/connectors/duo.py`
- **.validate_permissions()** (4 connections) — `app/connectors/duo.py`
- **.health_check()** (3 connections) — `app/connectors/duo.py`
- **.__init__()** (1 connections) — `app/connectors/duo.py`
- **Any** (1 connections)
- **Connector** (1 connections)
- **Fetch MFA authentication logs from Duo Admin API.** (1 connections) — `app/connectors/duo.py`
- **Probe Duo API hostname reachability.** (1 connections) — `app/connectors/duo.py`
- **Validate Duo Admin credentials.** (1 connections) — `app/connectors/duo.py`
- **Cisco Duo Admin API telemetry connector for MFA verification. Credentials: -…** (1 connections) — `app/connectors/duo.py`
- **Generate Duo API HMAC-SHA1 signature.** (1 connections) — `app/connectors/duo.py`
- **Validate Duo API credentials via /admin/v1/ping.** (1 connections) — `app/connectors/duo.py`

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (8 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (2 shared connections)

## Source Files

- `app/connectors/duo.py`

## Audit Trail

- EXTRACTED: 23 (82%)
- INFERRED: 5 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*