# router.py

> 46 nodes · cohesion 0.09

## Key Concepts

- **router.py** (37 connections) — `app/api/clinic/router.py`
- **test_moment_lifecycle.py** (19 connections) — `tests/services/clinic_engine/test_moment_lifecycle.py`
- **MomentRepository** (15 connections) — `app/services/clinic_engine/v2/moment_repository.py`
- **get_clinic_readiness()** (14 connections) — `app/api/clinic/router.py`
- **MomentStatus** (13 connections) — `app/models/clinic_moment.py`
- **fix_problem()** (11 connections) — `app/api/clinic/router.py`
- **ClinicMomentRecord** (10 connections) — `app/models/clinic_moment.py`
- **get_morning_summary()** (9 connections) — `app/api/clinic/router.py`
- **moment_repository.py** (9 connections) — `app/services/clinic_engine/v2/moment_repository.py`
- **_fetch_persisted_telemetry()** (8 connections) — `app/api/clinic/router.py`
- **create_mock_moment_record()** (8 connections) — `tests/services/clinic_engine/test_moment_lifecycle.py`
- **get_demo_telemetry()** (7 connections) — `app/api/clinic/router.py`
- **clinic_moment.py** (7 connections) — `app/models/clinic_moment.py`
- **test_fix_valid_moment()** (7 connections) — `tests/services/clinic_engine/test_moment_lifecycle.py`
- **.list_all()** (6 connections) — `app/services/clinic_engine/v2/providers/base.py`
- **test_stale_moment_cannot_execute()** (5 connections) — `tests/services/clinic_engine/test_moment_lifecycle.py`
- **Session** (4 connections)
- **.get_moment()** (4 connections) — `app/services/clinic_engine/v2/moment_repository.py`
- **.save_moments()** (4 connections) — `app/services/clinic_engine/v2/moment_repository.py`
- **test_duplicate_fix_requests_are_idempotent()** (4 connections) — `tests/services/clinic_engine/test_moment_lifecycle.py`
- **models/base.py** (3 connections) — `app/models/base.py`
- **.mark_resolved()** (3 connections) — `app/services/clinic_engine/v2/moment_repository.py`
- **db_session()** (3 connections) — `tests/services/clinic_engine/test_moment_lifecycle.py`
- **fixture** (3 connections)
- **setup_db()** (3 connections) — `tests/services/clinic_engine/test_moment_lifecycle.py`
- *... and 21 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (11 shared connections)
- [schema.py](schema.py.md) (10 shared connections)
- [ClinicMoment](ClinicMoment.md) (8 shared connections)
- [EvidenceKind](EvidenceKind.md) (5 shared connections)
- [contracts.py](contracts.py.md) (5 shared connections)
- [PilotService](PilotService.md) (4 shared connections)
- [MetricsEngine](MetricsEngine.md) (4 shared connections)
- [Evidence](Evidence.md) (4 shared connections)
- [main.py](main.py.md) (3 shared connections)
- [Organization](Organization.md) (3 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (2 shared connections)
- [User](User.md) (2 shared connections)

## Source Files

- `app/api/clinic/router.py`
- `app/models/base.py`
- `app/models/clinic_moment.py`
- `app/services/clinic_engine/v2/moment_repository.py`
- `app/services/clinic_engine/v2/providers/base.py`
- `tests/services/clinic_engine/test_moment_lifecycle.py`

## Audit Trail

- EXTRACTED: 137 (89%)
- INFERRED: 17 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*