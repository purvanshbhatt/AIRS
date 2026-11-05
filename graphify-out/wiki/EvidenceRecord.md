# EvidenceRecord

> 23 nodes · cohesion 0.10

## Key Concepts

- **EvidenceRecord** (26 connections) — `app/services/evidence/base_adapter.py`
- **_OkAdapter** (12 connections) — `tests/test_evidence_adapter_base.py`
- **Any** (5 connections)
- **.normalize()** (4 connections) — `app/services/evidence/adapters/splunk.py`
- **.normalize()** (4 connections) — `app/services/evidence/base_adapter.py`
- **.process_webhook()** (4 connections) — `app/services/evidence/base_adapter.py`
- **.process_upload()** (3 connections) — `app/services/evidence/base_adapter.py`
- **.expected_schema()** (3 connections) — `app/services/evidence/base_adapter.py`
- **.to_dict()** (2 connections) — `app/services/evidence/base_adapter.py`
- **.to_dict()** (2 connections) — `app/services/evidence/base_adapter.py`
- **.fetch_evidence()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.health()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **.normalize()** (2 connections) — `tests/test_evidence_adapter_base.py`
- **Any** (1 connections)
- **Splunk payloads have already been normalised by the ``SplunkConnector`` +…** (1 connections) — `app/services/evidence/adapters/splunk.py`
- **Translate vendor-specific payloads to canonical records. Used by tests and…** (1 connections) — `app/services/evidence/base_adapter.py`
- **JSON Schema definition of the expected webhook payload.** (1 connections) — `app/services/evidence/base_adapter.py`
- **Validate and normalize an incoming webhook payload into EvidenceRecords.** (1 connections) — `app/services/evidence/base_adapter.py`
- **Process an uploaded file and extract canonical EvidenceRecords.** (1 connections) — `app/services/evidence/base_adapter.py`
- **Vendor-neutral canonical evidence shape. Onward consumers (Verification Engine,…** (1 connections) — `app/services/evidence/base_adapter.py`
- **.connector_name()** (1 connections) — `tests/test_evidence_adapter_base.py`
- **EvidenceAdapter** (1 connections)
- **A minimal valid adapter used by the tests.** (1 connections) — `tests/test_evidence_adapter_base.py`

## Relationships

- [EvidenceAdapter](EvidenceAdapter.md) (10 shared connections)
- [WazuhAdapter](WazuhAdapter.md) (5 shared connections)
- [EvidenceRegistry](EvidenceRegistry.md) (5 shared connections)
- [SplunkAdapter](SplunkAdapter.md) (4 shared connections)
- [AWSSecurityHubAdapter](AWSSecurityHubAdapter.md) (3 shared connections)
- [AdapterHealth](AdapterHealth.md) (2 shared connections)
- [test_connectors_confidence_api.py](test_connectors_confidence_api.py.md) (2 shared connections)

## Source Files

- `app/services/evidence/adapters/splunk.py`
- `app/services/evidence/base_adapter.py`
- `tests/test_evidence_adapter_base.py`

## Audit Trail

- EXTRACTED: 52 (93%)
- INFERRED: 4 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*