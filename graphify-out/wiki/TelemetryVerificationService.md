# TelemetryVerificationService

> 168 nodes · cohesion 0.02

## Key Concepts

- **TelemetryVerificationService** (65 connections) — `app/services/telemetry.py`
- **staging_real_customer_e2e.py** (46 connections) — `scripts/staging_real_customer_e2e.py`
- **test_telemetry_verification.py** (35 connections) — `tests/test_telemetry_verification.py`
- **FindingProvenance** (34 connections) — `app/models/finding_provenance.py`
- **services/telemetry.py** (28 connections) — `app/services/telemetry.py`
- **test_governance_ingestion.py** (25 connections) — `tests/governance/test_governance_ingestion.py`
- **ProvenanceStatus** (20 connections) — `app/models/finding_provenance.py`
- **v1/telemetry.py** (19 connections) — `app/api/v1/telemetry.py`
- **SIEMEventPayload** (17 connections) — `app/services/telemetry.py`
- **run_e2e_validation()** (16 connections) — `scripts/staging_real_customer_e2e.py`
- **ControlRuleRegistry** (13 connections) — `app/models/control_rule_registry.py`
- **finding_provenance.py** (13 connections) — `app/models/finding_provenance.py`
- **VerificationSource** (12 connections) — `app/models/finding_provenance.py`
- **_make_payload()** (12 connections) — `tests/test_telemetry_verification.py`
- **ScoreAuditLog** (11 connections) — `app/models/score_audit_log.py`
- **TestSIEMEventProcessing** (11 connections) — `tests/test_telemetry_verification.py`
- **TestModelIntegrity** (10 connections) — `tests/test_telemetry_verification.py`
- **ingest_siem_event()** (9 connections) — `app/api/v1/telemetry.py`
- **VerificationResponse** (9 connections) — `app/services/telemetry.py`
- **TestGHIRecomputation** (9 connections) — `tests/test_telemetry_verification.py`
- **control_rule_registry.py** (8 connections) — `app/models/control_rule_registry.py`
- **TestDeterministicIngestionStateTransition** (8 connections) — `tests/governance/test_governance_ingestion.py`
- **._compute_evidence_hash()** (7 connections) — `app/services/telemetry.py`
- **.process_siem_event()** (7 connections) — `app/services/telemetry.py`
- **TestEndToEnd** (7 connections) — `tests/test_telemetry_verification.py`
- *... and 143 more nodes in this community*

## Relationships

- [Organization](Organization.md) (94 shared connections)
- [app/db/database.py](app-db-database.py.md) (18 shared connections)
- [FrameworkMappingRegistry](FrameworkMappingRegistry.md) (8 shared connections)
- [calculate_scores](calculate_scores.md) (7 shared connections)
- [_make_org](_make_org.md) (6 shared connections)
- [Connector](Connector.md) (6 shared connections)
- [ContinuousScoringEngine](ContinuousScoringEngine.md) (3 shared connections)
- [BaseModel](BaseModel.md) (3 shared connections)
- [EvidenceLedger](EvidenceLedger.md) (3 shared connections)
- [services/readiness_ledger.py](services-readiness_ledger.py.md) (3 shared connections)
- [external.py](external.py.md) (2 shared connections)
- [verify_webhook_signature](verify_webhook_signature.md) (2 shared connections)

## Source Files

- `app/api/v1/telemetry.py`
- `app/models/control_rule_registry.py`
- `app/models/finding_provenance.py`
- `app/models/score_audit_log.py`
- `app/services/telemetry.py`
- `scripts/staging_real_customer_e2e.py`
- `tests/governance/test_governance_ingestion.py`
- `tests/test_real_customer_e2e.py`
- `tests/test_telemetry_verification.py`

## Audit Trail

- EXTRACTED: 398 (86%)
- INFERRED: 66 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*