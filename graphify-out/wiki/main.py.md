# main.py

> 114 nodes · cohesion 0.02

## Key Concepts

- **main.py** (75 connections) — `app/main.py`
- **core/config.py** (52 connections) — `app/core/config.py`
- **test_dr_failure_simulation.py** (24 connections) — `tests/test_dr_failure_simulation.py`
- **test_multicloud_portability.py** (18 connections) — `tests/test_multicloud_portability.py`
- **Environment** (17 connections) — `app/core/config.py`
- **internal.py** (16 connections) — `app/api/internal.py`
- **test_health_multi_cloud.py** (15 connections) — `tests/test_health_multi_cloud.py`
- **CloudProvider** (8 connections) — `app/core/config.py`
- **forensic_trail.py** (8 connections) — `app/services/forensic_trail.py`
- **validate_deployment()** (7 connections) — `app/core/config.py`
- **get_replica_db()** (7 connections) — `app/db/database.py`
- **run_igvf_validation()** (6 connections) — `app/api/internal.py`
- **run_igvf_validation_all()** (6 connections) — `app/api/internal.py`
- **DeploymentValidationError** (6 connections) — `app/core/config.py`
- **upload_and_sign_pdf()** (6 connections) — `app/core/gcs.py`
- **lifespan()** (6 connections) — `app/main.py`
- **get** (6 connections)
- **tracing.py** (6 connections) — `app/observability/tracing.py`
- **TestStandbyLockGuarantees** (6 connections) — `tests/test_dr_failure_simulation.py`
- **register_system_auditor()** (5 connections) — `app/services/audit.py`
- **TestDisasterRecoveryStandbyLock** (5 connections) — `tests/test_health_multi_cloud.py`
- **.is_aws_standby_locked()** (4 connections) — `app/core/config.py`
- **gcs.py** (4 connections) — `app/core/gcs.py`
- **debug_ip()** (4 connections) — `app/main.py`
- **stop_intelligence_scheduler()** (4 connections) — `app/tasks/intelligence_task.py`
- *... and 89 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (48 shared connections)
- [Organization](Organization.md) (21 shared connections)
- [middleware.py](middleware.py.md) (7 shared connections)
- [test_reliability.py](test_reliability.py.md) (6 shared connections)
- [WazuhConfig](WazuhConfig.md) (6 shared connections)
- [_make_org](_make_org.md) (5 shared connections)
- [health.py](health.py.md) (5 shared connections)
- [Settings](Settings.md) (5 shared connections)
- [router.py](router.py.md) (3 shared connections)
- [ForensicTrailAgent](ForensicTrailAgent.md) (3 shared connections)
- [get_rubric](get_rubric.md) (3 shared connections)
- [get_allowed_origins](get_allowed_origins.md) (2 shared connections)

## Source Files

- `app/api/internal.py`
- `app/core/config.py`
- `app/core/gcs.py`
- `app/db/database.py`
- `app/main.py`
- `app/observability/tracing.py`
- `app/services/audit.py`
- `app/services/forensic_trail.py`
- `app/tasks/intelligence_task.py`
- `export_openapi.py`
- `export_report.py`
- `scripts/verify_aws_standby_runtime.py`
- `tests/test_dr_failure_simulation.py`
- `tests/test_health_multi_cloud.py`
- `tests/test_multicloud_portability.py`

## Audit Trail

- EXTRACTED: 313 (98%)
- INFERRED: 5 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*