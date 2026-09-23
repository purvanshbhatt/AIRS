# ReadinessLedgerEntry

> 18 nodes · cohesion 0.17

## Key Concepts

- **ReadinessLedgerEntry** (32 connections) — `app/models/readiness_ledger.py`
- **TestReadinessLedgerEntryModel** (9 connections) — `tests/test_readiness_ledger_model.py`
- **test_readiness_ledger_model.py** (5 connections) — `tests/test_readiness_ledger_model.py`
- **_make_org()** (5 connections) — `tests/test_readiness_ledger_model.py`
- **.test_default_uuid_on_insert()** (3 connections) — `tests/test_readiness_ledger_model.py`
- **.test_round_trip()** (3 connections) — `tests/test_readiness_ledger_model.py`
- **.test_timestamp_defaults_to_now()** (3 connections) — `tests/test_readiness_ledger_model.py`
- **._validate_score_range()** (2 connections) — `app/models/readiness_ledger.py`
- **.test_foreign_key_required()** (2 connections) — `tests/test_readiness_ledger_model.py`
- **.test_score_range_validator_rejects_above_100()** (2 connections) — `tests/test_readiness_ledger_model.py`
- **.test_score_range_validator_rejects_below_0()** (2 connections) — `tests/test_readiness_ledger_model.py`
- **Base** (1 connections)
- **Immutable readiness score-change ledger. Design Rationale: - previous_score /…** (1 connections) — `app/models/readiness_ledger.py`
- **.__repr__()** (1 connections) — `app/models/readiness_ledger.py`
- **Tests for ReadinessLedgerEntry (Sprint 1.8, Task S1.8-A1). Verifies: - Model…** (1 connections) — `tests/test_readiness_ledger_model.py`
- **.test_idempotency_index_columns()** (1 connections) — `tests/test_readiness_ledger_model.py`
- **.test_indexes_present()** (1 connections) — `tests/test_readiness_ledger_model.py`
- **validates** (1 connections)

## Relationships

- [Organization](Organization.md) (9 shared connections)
- [test_readiness_api.py](test_readiness_api.py.md) (5 shared connections)
- [services/readiness_ledger.py](services-readiness_ledger.py.md) (4 shared connections)
- [v1/readiness.py](v1-readiness.py.md) (2 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (2 shared connections)
- [calculate_readiness_delta](calculate_readiness_delta.md) (1 shared connections)

## Source Files

- `app/models/readiness_ledger.py`
- `tests/test_readiness_ledger_model.py`

## Audit Trail

- EXTRACTED: 42 (86%)
- INFERRED: 7 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*