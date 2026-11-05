# services/readiness_ledger.py

> 25 nodes · cohesion 0.12

## Key Concepts

- **services/readiness_ledger.py** (17 connections) — `app/services/readiness_ledger.py`
- **record_score_change()** (14 connections) — `app/services/readiness_ledger.py`
- **test_ledger_write_hook.py** (11 connections) — `tests/test_ledger_write_hook.py`
- **TestRecordScoreChange** (6 connections) — `tests/test_ledger_write_hook.py`
- **score_and_record()** (5 connections) — `app/services/readiness_ledger.py`
- **_make_org()** (4 connections) — `tests/test_ledger_write_hook.py`
- **attach_to_scoring()** (3 connections) — `app/services/readiness_ledger.py`
- **datetime** (3 connections)
- **__source_text()** (3 connections) — `app/services/readiness_ledger.py`
- **_utc_now()** (3 connections) — `app/services/readiness_ledger.py`
- **__verify_no_llm_imports()** (3 connections) — `app/services/readiness_ledger.py`
- **.test_basic_insert_and_idempotency()** (3 connections) — `tests/test_ledger_write_hook.py`
- **.test_distinct_write_creates_second_row()** (3 connections) — `tests/test_ledger_write_hook.py`
- **readiness_ledger_module_marker()** (2 connections) — `app/services/readiness_ledger.py`
- **TestModuleInvariants** (2 connections) — `tests/test_ledger_write_hook.py`
- **.test_invalid_org_id_raises()** (2 connections) — `tests/test_ledger_write_hook.py`
- **.test_score_range_rejection_through_validator()** (2 connections) — `tests/test_ledger_write_hook.py`
- **Any** (1 connections)
- **Readiness Ledger Write Hook. Per ADR-008, every score recalculation must…** (1 connections) — `app/services/readiness_ledger.py`
- **Insert a single immutable ledger row. Idempotent on ``(org_id, timestamp,…** (1 connections) — `app/services/readiness_ledger.py`
- **Wrap ``calculate_readiness_delta`` with a ledger write. Behavior: - The wrapped…** (1 connections) — `app/services/readiness_ledger.py`
- **Convenience scoring entrypoint that also writes a ledger row. Combines scoring…** (1 connections) — `app/services/readiness_ledger.py`
- **Runtime belt-and-suspenders check. The hard invariant (ADR-007) is that…** (1 connections) — `app/services/readiness_ledger.py`
- **Tests for the Readiness Ledger write hook (Sprint 1.8, Task S1.8-A4). Covers: -…** (1 connections) — `tests/test_ledger_write_hook.py`
- **.test_no_forbidden_llm_imports_in_source()** (1 connections) — `tests/test_ledger_write_hook.py`

## Relationships

- [Organization](Organization.md) (7 shared connections)
- [ReadinessLedgerEntry](ReadinessLedgerEntry.md) (4 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (3 shared connections)
- [calculate_readiness_delta](calculate_readiness_delta.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [calculate_scores](calculate_scores.md) (1 shared connections)

## Source Files

- `app/services/readiness_ledger.py`
- `tests/test_ledger_write_hook.py`

## Audit Trail

- EXTRACTED: 55 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*