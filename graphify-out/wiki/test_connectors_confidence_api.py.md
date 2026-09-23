# test_connectors_confidence_api.py

> 19 nodes · cohesion 0.17

## Key Concepts

- **test_connectors_confidence_api.py** (17 connections) — `tests/test_connectors_confidence_api.py`
- **get_instance()** (14 connections) — `app/services/evidence/registry.py`
- **test_evidence_adapter_base.py** (14 connections) — `tests/test_evidence_adapter_base.py`
- **reset_instance()** (9 connections) — `app/services/evidence/registry.py`
- **mock_registry()** (6 connections) — `tests/test_connectors_confidence_api.py`
- **TestSingleton** (4 connections) — `tests/test_evidence_adapter_base.py`
- **auth_override()** (3 connections) — `tests/test_connectors_confidence_api.py`
- **auth_override_missing_org()** (3 connections) — `tests/test_connectors_confidence_api.py`
- **fixture** (3 connections)
- **.test_get_instance_singleton()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.test_get_instance_singleton_is_empty_by_default()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.test_reset_instance_discardes()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **test_connectors_confidence_api_success()** (2 connections) — `tests/test_connectors_confidence_api.py`
- **TestModuleInvariants** (2 connections) — `tests/test_evidence_adapter_base.py`
- **Return the process-wide ``EvidenceRegistry`` singleton.** (1 connections) — `app/services/evidence/registry.py`
- **Discard the singleton (used by tests).** (1 connections) — `app/services/evidence/registry.py`
- **test_connectors_confidence_api_missing_org()** (1 connections) — `tests/test_connectors_confidence_api.py`
- **Tests for Sprint 1.8, Task S1.8-C1 — EvidenceAdapter ABC + Registry. Covers: -…** (1 connections) — `tests/test_evidence_adapter_base.py`
- **.test_no_forbidden_llm_imports()** (1 connections) — `tests/test_evidence_adapter_base.py`

## Relationships

- [EvidenceAdapter](EvidenceAdapter.md) (8 shared connections)
- [AdapterHealth](AdapterHealth.md) (6 shared connections)
- [EvidenceRegistry](EvidenceRegistry.md) (5 shared connections)
- [User](User.md) (3 shared connections)
- [connectors.py](connectors.py.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [EvidenceRecord](EvidenceRecord.md) (2 shared connections)
- [ConnectorManager](ConnectorManager.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)
- [main.py](main.py.md) (1 shared connections)

## Source Files

- `app/services/evidence/registry.py`
- `tests/test_connectors_confidence_api.py`
- `tests/test_evidence_adapter_base.py`

## Audit Trail

- EXTRACTED: 60 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*