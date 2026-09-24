# get_db()

> God node · 76 connections · `app/db/database.py`

**Community:** [app/db/database.py](app-db-database.py.md)

## Connections by Relation

### calls
- [SessionLocal](SessionLocal.md) `INFERRED`
- .test_full_failover_simulation() `EXTRACTED`
- .test_gated_failback_and_standby_relock() `EXTRACTED`
- .test_standby_error_response_format_is_safe_and_structured() `EXTRACTED`
- .test_regression_standby_cannot_accidentally_become_writable() `EXTRACTED`
- .test_standby_lock_enforces_503_on_get_db() `EXTRACTED`
- .test_standby_unlock_requires_explicit_boolean_flag() `EXTRACTED`
- .test_standby_lock_before_restore() `EXTRACTED`
- .test_standby_unlock_after_restore() `EXTRACTED`
- .test_aws_standby_database_locked() `EXTRACTED`
- .test_aws_standby_database_unlocked_when_restored() `EXTRACTED`
- run_runtime_verification() `EXTRACTED`

### contains
- [app/db/database.py](app-db-database.py.md) `EXTRACTED`

### imports
- assessments.py `EXTRACTED`
- [organizations.py](organizations.py.md) `EXTRACTED`
- [api/integrations.py](api-integrations.py.md) `EXTRACTED`
- test_governance.py `EXTRACTED`
- v1/integrations.py `EXTRACTED`
- [connectors.py](connectors.py.md) `EXTRACTED`
- [test_reliability.py](test_reliability.py.md) `EXTRACTED`
- [api/verification.py](api-verification.py.md) `EXTRACTED`
- api/reliability.py `EXTRACTED`
- governance.py `EXTRACTED`
- test_igvf.py `EXTRACTED`
- [router.py](router.py.md) `EXTRACTED`
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) `EXTRACTED`
- [sentinel.py](sentinel.py.md) `EXTRACTED`
- [inventory.py](inventory.py.md) `EXTRACTED`
- drift.py `EXTRACTED`
- [policies.py](policies.py.md) `EXTRACTED`
- [v1/readiness.py](v1-readiness.py.md) `EXTRACTED`
- narratives.py `EXTRACTED`
- remediations.py `EXTRACTED`

### indirect_call
- .is_aws_standby_locked() `INFERRED`

### rationale_for
- Dependency to get primary database session (Read/Write). In AWS Standby mode… `EXTRACTED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*