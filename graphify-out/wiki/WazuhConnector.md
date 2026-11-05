# WazuhConnector

> 22 nodes · cohesion 0.14

## Key Concepts

- **WazuhConnector** (21 connections) — `app/connectors/wazuh.py`
- **.sync()** (7 connections) — `app/connectors/wazuh.py`
- **._fetch_alerts()** (6 connections) — `app/connectors/wazuh.py`
- **._fetch_vulnerabilities()** (6 connections) — `app/connectors/wazuh.py`
- **._fetch_agents()** (5 connections) — `app/connectors/wazuh.py`
- **.validate_permissions()** (5 connections) — `app/connectors/wazuh.py`
- **._auth_headers()** (4 connections) — `app/connectors/wazuh.py`
- **AsyncClient** (3 connections)
- **.authenticate()** (3 connections) — `app/connectors/wazuh.py`
- **.health_check()** (3 connections) — `app/connectors/wazuh.py`
- **._map_level_to_severity()** (3 connections) — `app/connectors/wazuh.py`
- **._map_severity()** (2 connections) — `app/connectors/wazuh.py`
- **Connector** (1 connections)
- **Fetch agent status, vulnerabilities, and recent alerts.** (1 connections) — `app/connectors/wazuh.py`
- **Fetch Wazuh agent status for endpoint visibility.** (1 connections) — `app/connectors/wazuh.py`
- **Fetch vulnerability assessments across all agents.** (1 connections) — `app/connectors/wazuh.py`
- **Fetch recent security alerts (last 24h).** (1 connections) — `app/connectors/wazuh.py`
- **Validate Wazuh API user has required permissions.** (1 connections) — `app/connectors/wazuh.py`
- **Wazuh SIEM connector for verified security telemetry. Connects to the Wazuh…** (1 connections) — `app/connectors/wazuh.py`
- **Map Wazuh rule level (1-15) to standard severity.** (1 connections) — `app/connectors/wazuh.py`
- **Authenticate via Wazuh Manager /security/user/authenticate or API token.** (1 connections) — `app/connectors/wazuh.py`
- **.__init__()** (1 connections) — `app/connectors/wazuh.py`

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (7 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (7 shared connections)

## Source Files

- `app/connectors/wazuh.py`

## Audit Trail

- EXTRACTED: 41 (89%)
- INFERRED: 5 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*