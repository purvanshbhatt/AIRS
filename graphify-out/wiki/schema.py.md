# schema.py

> 92 nodes · cohesion 0.05

## Key Concepts

- **schema.py** (41 connections) — `app/services/clinic_engine/v2/schema.py`
- **test_v2_engine.py** (35 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **EvaluationResult** (33 connections) — `app/services/clinic_engine/v2/schema.py`
- **Verdict** (31 connections) — `app/services/clinic_engine/v2/schema.py`
- **BaseCapability** (26 connections) — `app/services/clinic_engine/v2/capability.py`
- **MomentTranslation** (24 connections) — `app/services/clinic_engine/v2/schema.py`
- **ActionIntent** (21 connections) — `app/services/clinic_engine/v2/schema.py`
- **DeviceCompromiseCapability** (20 connections) — `app/services/clinic_engine/v2/capabilities/device_compromise.py`
- **RecoveryReadinessCapability** (20 connections) — `app/services/clinic_engine/v2/capabilities/recovery_readiness.py`
- **UnauthorizedAccessCapability** (20 connections) — `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- **capability.py** (17 connections) — `app/services/clinic_engine/v2/capability.py`
- **TestDeviceCompromise** (14 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **device_compromise.py** (13 connections) — `app/services/clinic_engine/v2/capabilities/device_compromise.py`
- **recovery_readiness.py** (13 connections) — `app/services/clinic_engine/v2/capabilities/recovery_readiness.py`
- **unauthorized_access.py** (13 connections) — `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- **CapabilityRegistry** (13 connections) — `app/services/clinic_engine/v2/capability.py`
- **v2/engine.py** (11 connections) — `app/services/clinic_engine/v2/engine.py`
- **.evaluate()** (9 connections) — `app/services/clinic_engine/v2/capabilities/device_compromise.py`
- **test_security_serialization.py** (7 connections) — `tests/services/clinic_engine/test_security_serialization.py`
- **test_evidence_ids_never_serialized()** (7 connections) — `tests/services/clinic_engine/test_security_serialization.py`
- **capabilities/__init__.py** (6 connections) — `app/services/clinic_engine/v2/capabilities/__init__.py`
- **.translate()** (4 connections) — `app/services/clinic_engine/v2/capabilities/device_compromise.py`
- **.translate()** (4 connections) — `app/services/clinic_engine/v2/capabilities/recovery_readiness.py`
- **.get_actions()** (4 connections) — `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- **.translate()** (4 connections) — `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- *... and 67 more nodes in this community*

## Relationships

- [Evidence](Evidence.md) (44 shared connections)
- [EvidenceKind](EvidenceKind.md) (30 shared connections)
- [ClinicMoment](ClinicMoment.md) (16 shared connections)
- [router.py](router.py.md) (10 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (9 shared connections)
- [contracts.py](contracts.py.md) (9 shared connections)
- [test_explainability.py](test_explainability.py.md) (6 shared connections)
- [BaseModel](BaseModel.md) (3 shared connections)
- [MetricsEngine](MetricsEngine.md) (2 shared connections)
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (1 shared connections)

## Source Files

- `app/services/clinic_engine/v2/capabilities/__init__.py`
- `app/services/clinic_engine/v2/capabilities/device_compromise.py`
- `app/services/clinic_engine/v2/capabilities/recovery_readiness.py`
- `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- `app/services/clinic_engine/v2/capability.py`
- `app/services/clinic_engine/v2/engine.py`
- `app/services/clinic_engine/v2/schema.py`
- `tests/services/clinic_engine/test_security_serialization.py`
- `tests/services/clinic_engine/test_v2_engine.py`

## Audit Trail

- EXTRACTED: 284 (86%)
- INFERRED: 48 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*