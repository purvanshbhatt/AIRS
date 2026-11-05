# AdapterHealth

> 28 nodes · cohesion 0.12

## Key Concepts

- **AdapterHealth** (40 connections) — `app/services/evidence/base_adapter.py`
- **calculate_evidence_confidence()** (14 connections) — `app/services/evidence_confidence.py`
- **MockAdapter** (10 connections) — `tests/test_connectors_confidence_api.py`
- **test_evidence_confidence.py** (10 connections) — `tests/test_evidence_confidence.py`
- **evidence_confidence.py** (5 connections) — `app/services/evidence_confidence.py`
- **TestAdapterHealthHelper** (4 connections) — `tests/test_evidence_adapter_base.py`
- **.health()** (3 connections) — `app/services/evidence/base_adapter.py`
- **test_evidence_confidence_completeness()** (3 connections) — `tests/test_evidence_confidence.py`
- **test_evidence_confidence_freshness_decay()** (3 connections) — `tests/test_evidence_confidence.py`
- **test_evidence_confidence_never_successful()** (3 connections) — `tests/test_evidence_confidence.py`
- **test_evidence_confidence_perfect()** (3 connections) — `tests/test_evidence_confidence.py`
- **test_evidence_confidence_success_rate()** (3 connections) — `tests/test_evidence_confidence.py`
- **test_evidence_confidence_unhealthy()** (3 connections) — `tests/test_evidence_confidence.py`
- **datetime** (2 connections)
- **.health()** (2 connections) — `tests/test_connectors_confidence_api.py`
- **.__init__()** (2 connections) — `tests/test_connectors_confidence_api.py`
- **.test_success_rate_computed()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.test_success_rate_no_probes_is_zero()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.test_to_dict_shape()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.success_rate()** (1 connections) — `app/services/evidence/base_adapter.py`
- **Report live adapter health for the Evidence Confidence engine.** (1 connections) — `app/services/evidence/base_adapter.py`
- **Health snapshot used by Evidence Confidence (ADR-010).** (1 connections) — `app/services/evidence/base_adapter.py`
- **Any** (1 connections)
- **Calculate Evidence Confidence score (0-100) based on four deterministic…** (1 connections) — `app/services/evidence_confidence.py`
- **.connector_name()** (1 connections) — `tests/test_connectors_confidence_api.py`
- *... and 3 more nodes in this community*

## Relationships

- [EvidenceAdapter](EvidenceAdapter.md) (9 shared connections)
- [test_connectors_confidence_api.py](test_connectors_confidence_api.py.md) (6 shared connections)
- [SplunkAdapter](SplunkAdapter.md) (4 shared connections)
- [WazuhAdapter](WazuhAdapter.md) (4 shared connections)
- [connectors.py](connectors.py.md) (4 shared connections)
- [AWSSecurityHubAdapter](AWSSecurityHubAdapter.md) (2 shared connections)
- [EvidenceRecord](EvidenceRecord.md) (2 shared connections)

## Source Files

- `app/services/evidence/base_adapter.py`
- `app/services/evidence_confidence.py`
- `tests/test_connectors_confidence_api.py`
- `tests/test_evidence_adapter_base.py`
- `tests/test_evidence_confidence.py`

## Audit Trail

- EXTRACTED: 69 (88%)
- INFERRED: 9 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*