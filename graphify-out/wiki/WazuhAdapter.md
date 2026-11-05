# WazuhAdapter

> 22 nodes · cohesion 0.11

## Key Concepts

- **WazuhAdapter** (17 connections) — `app/services/evidence/adapters/wazuh.py`
- **test_wazuh_adapter.py** (17 connections) — `tests/test_wazuh_adapter.py`
- **mock_wazuh_client()** (6 connections) — `tests/test_wazuh_adapter.py`
- **.fetch_evidence()** (5 connections) — `app/services/evidence/adapters/wazuh.py`
- **.normalize()** (5 connections) — `app/services/evidence/adapters/wazuh.py`
- **.health()** (3 connections) — `app/services/evidence/adapters/wazuh.py`
- **asyncio** (3 connections)
- **test_wazuh_adapter_fetch_evidence()** (3 connections) — `tests/test_wazuh_adapter.py`
- **test_wazuh_adapter_health()** (3 connections) — `tests/test_wazuh_adapter.py`
- **wazuh_adapter()** (3 connections) — `tests/test_wazuh_adapter.py`
- **datetime** (2 connections)
- **.__init__()** (2 connections) — `app/services/evidence/adapters/wazuh.py`
- **fixture** (2 connections)
- **test_wazuh_adapter_conformance()** (2 connections) — `tests/test_wazuh_adapter.py`
- **test_wazuh_adapter_health_failure()** (2 connections) — `tests/test_wazuh_adapter.py`
- **Any** (1 connections)
- **EvidenceAdapter** (1 connections)
- **EvidenceAdapter implementation for Wazuh.** (1 connections) — `app/services/evidence/adapters/wazuh.py`
- **Fetch all evidence checks from Wazuh.** (1 connections) — `app/services/evidence/adapters/wazuh.py`
- **Convert Wazuh dictionaries to canonical EvidenceRecords.** (1 connections) — `app/services/evidence/adapters/wazuh.py`
- **Report live adapter health.** (1 connections) — `app/services/evidence/adapters/wazuh.py`
- **.connector_name()** (1 connections) — `app/services/evidence/adapters/wazuh.py`

## Relationships

- [WazuhConfig](WazuhConfig.md) (11 shared connections)
- [EvidenceAdapter](EvidenceAdapter.md) (8 shared connections)
- [EvidenceRecord](EvidenceRecord.md) (5 shared connections)
- [AdapterHealth](AdapterHealth.md) (4 shared connections)
- [ConnectorManager](ConnectorManager.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)

## Source Files

- `app/services/evidence/adapters/wazuh.py`
- `tests/test_wazuh_adapter.py`

## Audit Trail

- EXTRACTED: 45 (80%)
- INFERRED: 11 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*