# test_evidence_integrity.py

> 34 nodes · cohesion 0.10

## Key Concepts

- **test_evidence_integrity.py** (28 connections) — `tests/test_evidence_integrity.py`
- **schemas/evidence.py** (13 connections) — `app/schemas/evidence.py`
- **compute_evidence_hash()** (12 connections) — `app/services/evidence/integrity.py`
- **verify_evidence_hash()** (12 connections) — `app/services/evidence/integrity.py`
- **EvidenceSeverity** (6 connections) — `app/schemas/evidence.py`
- **integrity.py** (6 connections) — `app/services/evidence/integrity.py`
- **EvidenceConfidence** (5 connections) — `app/schemas/evidence.py`
- **ProviderTransport** (5 connections) — `app/schemas/evidence.py`
- **canonicalize_payload()** (5 connections) — `app/services/evidence/integrity.py`
- **test_changed_nested_value_mismatch()** (4 connections) — `tests/test_evidence_integrity.py`
- **test_correct_payload_valid_hash()** (4 connections) — `tests/test_evidence_integrity.py`
- **test_modified_payload_hash_mismatch()** (4 connections) — `tests/test_evidence_integrity.py`
- **test_reordered_json_keys_preserve_identity()** (4 connections) — `tests/test_evidence_integrity.py`
- **.compute_hash()** (3 connections) — `app/schemas/evidence.py`
- **.verify_integrity()** (3 connections) — `app/schemas/evidence.py`
- **Enum** (3 connections)
- **Any** (3 connections)
- **test_malformed_evidence_handling()** (3 connections) — `tests/test_evidence_integrity.py`
- **str** (2 connections)
- **test_db()** (2 connections) — `tests/test_evidence_integrity.py`
- **Measures the veracity and quality of the collected evidence. Each dimension is…** (1 connections) — `app/schemas/evidence.py`
- **Deterministically hash the payload for the immutable ledger.** (1 connections) — `app/schemas/evidence.py`
- **Verify that the evidence_hash matches the authoritative payload.** (1 connections) — `app/schemas/evidence.py`
- **ResilAI Authoritative Evidence Integrity Verification Module. Enforces…** (1 connections) — `app/services/evidence/integrity.py`
- **Canonicalize a telemetry payload into a deterministic string representation.…** (1 connections) — `app/services/evidence/integrity.py`
- *... and 9 more nodes in this community*

## Relationships

- [EvidenceLedger](EvidenceLedger.md) (16 shared connections)
- [Connector](Connector.md) (5 shared connections)
- [connectors.py](connectors.py.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/schemas/evidence.py`
- `app/services/evidence/integrity.py`
- `tests/test_evidence_integrity.py`

## Audit Trail

- EXTRACTED: 85 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*