# TestWazuhClient

> 12 nodes · cohesion 0.20

## Key Concepts

- **TestWazuhClient** (9 connections) — `tests/test_siem_integrations.py`
- **.test_get_agent_status()** (4 connections) — `tests/test_siem_integrations.py`
- **.test_get_jwt_token_success()** (4 connections) — `tests/test_siem_integrations.py`
- **.test_get_vulnerabilities()** (4 connections) — `tests/test_siem_integrations.py`
- **.wazuh_client()** (4 connections) — `tests/test_siem_integrations.py`
- **patch** (3 connections)
- **fixture** (1 connections)
- **Test fetching vulnerabilities from Wazuh.** (1 connections) — `tests/test_siem_integrations.py`
- **Test suite for WazuhClient.** (1 connections) — `tests/test_siem_integrations.py`
- **Create a Wazuh client for testing.** (1 connections) — `tests/test_siem_integrations.py`
- **Test successful JWT token retrieval.** (1 connections) — `tests/test_siem_integrations.py`
- **Test fetching agent status from Wazuh.** (1 connections) — `tests/test_siem_integrations.py`

## Relationships

- [WazuhConfig](WazuhConfig.md) (4 shared connections)
- [asyncio](asyncio.md) (3 shared connections)
- [test_siem_integrations.py](test_siem_integrations.py.md) (1 shared connections)

## Source Files

- `tests/test_siem_integrations.py`

## Audit Trail

- EXTRACTED: 18 (86%)
- INFERRED: 3 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*