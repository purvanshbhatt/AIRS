# Evidence

> 50 nodes · cohesion 0.08

## Key Concepts

- **Evidence** (55 connections) — `app/services/clinic_engine/v2/schema.py`
- **ClinicEvaluationEngine** (19 connections) — `app/services/clinic_engine/v2/engine.py`
- **TestUnauthorizedAccess** (16 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **_iso()** (13 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **_now()** (13 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **TestRecoveryReadiness** (13 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **TestClinicEvaluationEngine** (11 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.evaluate()** (10 connections) — `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- **.evaluate()** (8 connections) — `app/services/clinic_engine/v2/capabilities/recovery_readiness.py`
- **.test_all_safe_empty()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_mixed_evidence_multiple_moments()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_backup_failed_26_hours_critical()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_backup_ok_4_hours_safe()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_incremental_16_hours_concern()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_active_user_safe()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_disabled_account_safe()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_null_last_sign_in_new_account_safe()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_null_last_sign_in_old_account_critical()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_stale_user_30_days_critical()** (6 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_full_pipeline_microsoft_provider_to_engine()** (5 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_stale_user_produces_moment()** (5 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.evaluate()** (4 connections) — `app/services/clinic_engine/v2/engine.py`
- **.test_no_backup_ever_critical()** (4 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.test_null_everything_concern()** (4 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **datetime** (3 connections)
- *... and 25 more nodes in this community*

## Relationships

- [schema.py](schema.py.md) (44 shared connections)
- [EvidenceKind](EvidenceKind.md) (19 shared connections)
- [router.py](router.py.md) (4 shared connections)
- [MetricsEngine](MetricsEngine.md) (2 shared connections)
- [ClinicMoment](ClinicMoment.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/services/clinic_engine/v2/capabilities/recovery_readiness.py`
- `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- `app/services/clinic_engine/v2/engine.py`
- `app/services/clinic_engine/v2/schema.py`
- `tests/services/clinic_engine/test_v2_engine.py`

## Audit Trail

- EXTRACTED: 144 (84%)
- INFERRED: 28 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*