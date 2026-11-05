# calculate_readiness_delta

> 27 nodes · cohesion 0.11

## Key Concepts

- **calculate_readiness_delta()** (29 connections) — `app/services/scoring.py`
- **project_readiness()** (9 connections) — `app/services/decision_engine.py`
- **TestCalculateReadinessDelta** (6 connections) — `tests/test_calculate_delta.py`
- **test_decision_drift_guard.py** (6 connections) — `tests/test_decision_drift_guard.py`
- **decision_engine.py** (5 connections) — `app/services/decision_engine.py`
- **test_calculate_delta.py** (5 connections) — `tests/test_calculate_delta.py`
- **TestScoringIsolationInvariant** (4 connections) — `tests/test_calculate_delta.py`
- **test_project_readiness_matches_actual_scoring()** (4 connections) — `tests/test_decision_drift_guard.py`
- **TestScoreAndRecordHook** (4 connections) — `tests/test_ledger_write_hook.py`
- **sprint1_6_demo.py** (3 connections) — `scripts/sprint1_6_demo.py`
- **.test_invariance_under_replay()** (3 connections) — `tests/test_ledger_write_hook.py`
- **.test_score_and_record_writes_ledger_row()** (3 connections) — `tests/test_ledger_write_hook.py`
- **run_demo()** (2 connections) — `scripts/sprint1_6_demo.py`
- **.test_final_score_clamped_between_0_and_100()** (2 connections) — `tests/test_calculate_delta.py`
- **.test_known_fixture_produces_expected_output()** (2 connections) — `tests/test_calculate_delta.py`
- **.test_no_previous_returns_none_delta()** (2 connections) — `tests/test_calculate_delta.py`
- **.test_repeated_calculation_determinism()** (2 connections) — `tests/test_calculate_delta.py`
- **.test_returns_documented_breakdown()** (2 connections) — `tests/test_calculate_delta.py`
- **.test_calculate_readiness_delta_signature_is_stable()** (2 connections) — `tests/test_calculate_delta.py`
- **Any** (1 connections)
- **Project readiness score based on proposed actions using deterministic scoring.…** (1 connections) — `app/services/decision_engine.py`
- **Readiness Impact Engine. Single source of readiness delta computation per…** (1 connections) — `app/services/scoring.py`
- **Tests for the deterministic scoring contract (Sprint 1.8, Task S1.8-A2).…** (1 connections) — `tests/test_calculate_delta.py`
- **.test_module_direct_imports_contain_no_forbidden_names()** (1 connections) — `tests/test_calculate_delta.py`
- **.test_module_source_has_no_forbidden_runtime_calls()** (1 connections) — `tests/test_calculate_delta.py`
- *... and 2 more nodes in this community*

## Relationships

- [calculate_scores](calculate_scores.md) (6 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [_get_current_state](_get_current_state.md) (3 shared connections)
- [services/readiness_ledger.py](services-readiness_ledger.py.md) (3 shared connections)
- [extract_drivers](extract_drivers.md) (2 shared connections)
- [validate_delta.py](validate_delta.py.md) (2 shared connections)
- [TestArchitecturalInvariantR4](TestArchitecturalInvariantR4.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [public.py](public.py.md) (1 shared connections)
- [ReadinessLedgerEntry](ReadinessLedgerEntry.md) (1 shared connections)

## Source Files

- `app/services/decision_engine.py`
- `app/services/scoring.py`
- `scripts/sprint1_6_demo.py`
- `tests/test_calculate_delta.py`
- `tests/test_decision_drift_guard.py`
- `tests/test_ledger_write_hook.py`

## Audit Trail

- EXTRACTED: 61 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*