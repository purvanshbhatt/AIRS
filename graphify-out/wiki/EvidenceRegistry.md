# EvidenceRegistry

> 25 nodes · cohesion 0.11

## Key Concepts

- **EvidenceRegistry** (22 connections) — `app/services/evidence/registry.py`
- **TestRegistryLookup** (7 connections) — `tests/test_evidence_adapter_base.py`
- **_MissingMethodsAdapter** (5 connections) — `tests/test_evidence_adapter_base.py`
- **TestABCEnforcement** (4 connections) — `tests/test_evidence_adapter_base.py`
- **EvidenceAdapter** (3 connections)
- **.test_register_accepts_valid_subclass()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.test_register_rejects_partial_subclass()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.test_get_adapter_returns_registered()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.test_list_connectors_returns_sorted()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.test_replace_existing()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.test_unregister_returns_true_for_known()** (3 connections) — `tests/test_evidence_adapter_base.py`
- **.adapters()** (2 connections) — `app/services/evidence/registry.py`
- **.get_adapter()** (2 connections) — `app/services/evidence/registry.py`
- **.register()** (2 connections) — `app/services/evidence/registry.py`
- **.test_register_rejects_non_abc()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.test_get_adapter_unknown_returns_none()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.test_unregister_returns_false_for_unknown()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.__init__()** (1 connections) — `app/services/evidence/registry.py`
- **.is_registered()** (1 connections) — `app/services/evidence/registry.py`
- **.list_connectors()** (1 connections) — `app/services/evidence/registry.py`
- **.unregister()** (1 connections) — `app/services/evidence/registry.py`
- **In-memory registry of ``EvidenceAdapter`` instances. Singleton-style access via…** (1 connections) — `app/services/evidence/registry.py`
- **.connector_name()** (1 connections) — `tests/test_evidence_adapter_base.py`
- **.fetch_evidence()** (1 connections) — `tests/test_evidence_adapter_base.py`
- **Missing abstract methods — should fail ``register``.** (1 connections) — `tests/test_evidence_adapter_base.py`

## Relationships

- [test_connectors_confidence_api.py](test_connectors_confidence_api.py.md) (5 shared connections)
- [EvidenceRecord](EvidenceRecord.md) (5 shared connections)
- [EvidenceAdapter](EvidenceAdapter.md) (3 shared connections)

## Source Files

- `app/services/evidence/registry.py`
- `tests/test_evidence_adapter_base.py`

## Audit Trail

- EXTRACTED: 45 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*