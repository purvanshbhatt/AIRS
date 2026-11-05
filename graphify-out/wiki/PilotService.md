# PilotService

> 52 nodes · cohesion 0.07

## Key Concepts

- **PilotService** (31 connections) — `app/services/clinic_engine/v2/pilot.py`
- **v2/pilot.py** (21 connections) — `app/services/clinic_engine/v2/pilot.py`
- **models/clinic/__init__.py** (19 connections) — `app/models/clinic/__init__.py`
- **CriticalSystem** (10 connections) — `app/models/clinic/critical_system.py`
- **ClinicDevice** (10 connections) — `app/models/clinic/device.py`
- **MSPRelationship** (10 connections) — `app/models/clinic/msp.py`
- **ClinicStaff** (10 connections) — `app/models/clinic/staff.py`
- **staff.py** (8 connections) — `app/models/clinic/staff.py`
- **.seed_demo_clinic()** (7 connections) — `app/services/clinic_engine/v2/pilot.py`
- **critical_system.py** (6 connections) — `app/models/clinic/critical_system.py`
- **device.py** (6 connections) — `app/models/clinic/device.py`
- **TestPilotServiceModeDefaults** (6 connections) — `tests/test_production_org_lifecycle.py`
- **HostingType** (5 connections) — `app/models/clinic/critical_system.py`
- **SystemType** (5 connections) — `app/models/clinic/critical_system.py`
- **DeviceType** (5 connections) — `app/models/clinic/device.py`
- **msp.py** (5 connections) — `app/models/clinic/msp.py`
- **MSPContractType** (5 connections) — `app/models/clinic/msp.py`
- **ReadinessSnapshot** (5 connections) — `app/models/clinic/readiness_snapshot.py`
- **ClinicDepartment** (5 connections) — `app/models/clinic/staff.py`
- **ClinicRole** (5 connections) — `app/models/clinic/staff.py`
- **EmploymentStatus** (5 connections) — `app/models/clinic/staff.py`
- **.get_mode()** (5 connections) — `app/services/clinic_engine/v2/pilot.py`
- **.test_explicit_demo_org_returns_demo()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_null_org_mode_returns_pilot()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **str** (3 connections)
- *... and 27 more nodes in this community*

## Relationships

- [Organization](Organization.md) (13 shared connections)
- [contracts.py](contracts.py.md) (10 shared connections)
- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [Connector](Connector.md) (7 shared connections)
- [router.py](router.py.md) (4 shared connections)
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) (4 shared connections)
- [api/integrations.py](api-integrations.py.md) (2 shared connections)
- [MetricsEngine](MetricsEngine.md) (1 shared connections)

## Source Files

- `app/models/clinic/__init__.py`
- `app/models/clinic/critical_system.py`
- `app/models/clinic/device.py`
- `app/models/clinic/msp.py`
- `app/models/clinic/readiness_snapshot.py`
- `app/models/clinic/staff.py`
- `app/services/clinic_engine/v2/pilot.py`
- `tests/test_production_org_lifecycle.py`

## Audit Trail

- EXTRACTED: 123 (85%)
- INFERRED: 21 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*