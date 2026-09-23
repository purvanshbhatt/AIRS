# WazuhConfig

> 76 nodes · cohesion 0.04

## Key Concepts

- **WazuhConfig** (36 connections) — `app/models/wazuh_config.py`
- **wazuh_client.py** (26 connections) — `app/services/wazuh_client.py`
- **WazuhClient** (26 connections) — `app/services/wazuh_client.py`
- **test_wazuh_persistence.py** (23 connections) — `tests/test_wazuh_persistence.py`
- **WazuhTelemetryCache** (21 connections) — `app/models/wazuh_telemetry_cache.py`
- **WazuhClientFactory** (19 connections) — `app/services/wazuh_client.py`
- **.get_client()** (14 connections) — `app/services/wazuh_client.py`
- **_decrypt_doc_fields()** (13 connections) — `app/db/firestore.py`
- **WazuhDiscoveryService** (13 connections) — `app/services/discovery/wazuh_discovery.py`
- **wazuh_config.py** (12 connections) — `app/models/wazuh_config.py`
- **wazuh_discovery.py** (11 connections) — `app/services/discovery/wazuh_discovery.py`
- **WazuhAgentStatusResponse** (11 connections) — `app/services/wazuh_client.py`
- **EncryptedString** (9 connections) — `app/db/types.py`
- **poll_wazuh_telemetry()** (9 connections) — `app/main.py`
- **WazuhVulnerabilitiesResponse** (8 connections) — `app/services/wazuh_client.py`
- **_wazuh_config_to_doc()** (7 connections) — `app/db/firestore.py`
- **.invalidate_client()** (7 connections) — `app/services/wazuh_client.py`
- **types.py** (6 connections) — `app/db/types.py`
- **._get()** (6 connections) — `app/services/wazuh_client.py`
- **setup_wazuh.py** (6 connections) — `scripts/setup_wazuh.py`
- **test_wazuh_client_factory_firestore_fallback()** (6 connections) — `tests/test_wazuh_persistence.py`
- **test_wazuh_client_factory_resolution()** (6 connections) — `tests/test_wazuh_persistence.py`
- **test_wazuh_telemetry_cache_fallback()** (6 connections) — `tests/test_wazuh_persistence.py`
- **.discover_from_wazuh()** (5 connections) — `app/services/discovery/wazuh_discovery.py`
- **AgentStatus** (5 connections) — `app/services/wazuh_client.py`
- *... and 51 more nodes in this community*

## Relationships

- [api/integrations.py](api-integrations.py.md) (20 shared connections)
- [Organization](Organization.md) (14 shared connections)
- [EncryptionService](EncryptionService.md) (13 shared connections)
- [get_user_org_id](get_user_org_id.md) (13 shared connections)
- [WazuhAdapter](WazuhAdapter.md) (11 shared connections)
- [discovery/orchestrator.py](discovery-orchestrator.py.md) (10 shared connections)
- [get_firestore_client](get_firestore_client.md) (9 shared connections)
- [BaseModel](BaseModel.md) (8 shared connections)
- [test_connector_progress.py](test_connector_progress.py.md) (7 shared connections)
- [test_siem_integrations.py](test_siem_integrations.py.md) (7 shared connections)
- [main.py](main.py.md) (6 shared connections)
- [app/db/database.py](app-db-database.py.md) (6 shared connections)

## Source Files

- `app/db/firestore.py`
- `app/db/types.py`
- `app/main.py`
- `app/models/wazuh_config.py`
- `app/models/wazuh_telemetry_cache.py`
- `app/services/discovery/wazuh_discovery.py`
- `app/services/wazuh_client.py`
- `scripts/setup_wazuh.py`
- `tests/test_wazuh_persistence.py`

## Audit Trail

- EXTRACTED: 231 (83%)
- INFERRED: 47 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*