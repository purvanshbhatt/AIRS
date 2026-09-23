# v1/control_verification.py

> 56 nodes · cohesion 0.06

## Key Concepts

- **v1/control_verification.py** (18 connections) — `app/api/v1/control_verification.py`
- **services/control_verification.py** (12 connections) — `app/services/control_verification.py`
- **VerificationService** (12 connections) — `app/services/control_verification.py`
- **test_verification.py** (11 connections) — `archive/scripts/test_verification.py`
- **get_verification_service()** (10 connections) — `app/api/v1/control_verification.py`
- **attest_control()** (9 connections) — `app/api/v1/control_verification.py`
- **ingest_telemetry_evidence()** (9 connections) — `app/api/v1/control_verification.py`
- **models/verification.py** (9 connections) — `app/models/verification.py`
- **VerificationResult** (9 connections) — `app/models/verification.py`
- **get_verification_summary()** (8 connections) — `app/api/v1/control_verification.py`
- **._audit_state_change()** (8 connections) — `app/services/control_verification.py`
- **.ingest_telemetry()** (7 connections) — `app/services/control_verification.py`
- **ControlEvidence** (6 connections) — `app/models/verification.py`
- **VerificationAuditLog** (6 connections) — `app/models/verification.py`
- **schemas/control_verification.py** (6 connections) — `app/schemas/control_verification.py`
- **.organization_id()** (5 connections) — `app/connectors/base.py`
- **VerificationConfidence** (5 connections) — `app/models/verification.py`
- **VerificationState** (5 connections) — `app/models/verification.py`
- **.attest_control()** (5 connections) — `app/services/control_verification.py`
- **.get_or_create_result()** (5 connections) — `app/services/control_verification.py`
- **test_verification_engine()** (5 connections) — `archive/scripts/test_verification.py`
- **Session** (4 connections)
- **User** (4 connections)
- **AttestRequest** (4 connections) — `app/schemas/control_verification.py`
- **TelemetryIngestRequest** (4 connections) — `app/schemas/control_verification.py`
- *... and 31 more nodes in this community*

## Relationships

- [Organization](Organization.md) (11 shared connections)
- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [User](User.md) (5 shared connections)
- [BaseModel](BaseModel.md) (5 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (2 shared connections)
- [Connector](Connector.md) (2 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (1 shared connections)
- [api/verification.py](api-verification.py.md) (1 shared connections)
- [SessionLocal](SessionLocal.md) (1 shared connections)

## Source Files

- `app/api/v1/control_verification.py`
- `app/connectors/base.py`
- `app/models/verification.py`
- `app/schemas/control_verification.py`
- `app/services/control_verification.py`
- `archive/scripts/test_verification.py`

## Audit Trail

- EXTRACTED: 125 (93%)
- INFERRED: 10 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*