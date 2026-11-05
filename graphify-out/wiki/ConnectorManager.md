# ConnectorManager

> 62 nodes · cohesion 0.05

## Key Concepts

- **ConnectorManager** (77 connections) — `app/services/connector_manager.py`
- **aws_integration/test_tenant_isolation.py** (12 connections) — `tests/aws_integration/test_tenant_isolation.py`
- **aws_integration/test_evidence_pipeline.py** (11 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **TestEvidencePipeline** (10 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **TestTenantIsolation** (9 connections) — `tests/aws_integration/test_tenant_isolation.py`
- **._ensure_adapter_registered()** (8 connections) — `app/services/connector_manager.py`
- **_create_test_connector()** (7 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **_create_test_org()** (7 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **.test_org_a_cannot_access_org_b_telemetry()** (7 connections) — `tests/aws_integration/test_tenant_isolation.py`
- **._decrypt_credentials()** (6 connections) — `app/services/connector_manager.py`
- **._ingest_events()** (6 connections) — `app/services/connector_manager.py`
- **_run()** (6 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **.test_events_create_telemetry_records()** (6 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **.test_no_credentials_in_telemetry_payload()** (6 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **.test_org_id_scoping()** (6 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **.test_telemetry_deduplication()** (6 connections) — `tests/aws_integration/test_evidence_pipeline.py`
- **.register_connector()** (5 connections) — `app/services/connector_manager.py`
- **_create_test_connector()** (5 connections) — `tests/aws_integration/test_tenant_isolation.py`
- **_create_test_org()** (5 connections) — `tests/aws_integration/test_tenant_isolation.py`
- **.test_connector_manager_enforces_org_scope()** (5 connections) — `tests/aws_integration/test_tenant_isolation.py`
- **.test_org_a_cannot_access_org_b_connector()** (5 connections) — `tests/aws_integration/test_tenant_isolation.py`
- **._encrypt_credentials()** (4 connections) — `app/services/connector_manager.py`
- **.get_connector()** (4 connections) — `app/services/connector_manager.py`
- **.health_check()** (4 connections) — `app/services/connector_manager.py`
- **.validate_permissions()** (4 connections) — `app/services/connector_manager.py`
- *... and 37 more nodes in this community*

## Relationships

- [Connector](Connector.md) (25 shared connections)
- [connectors.py](connectors.py.md) (15 shared connections)
- [Organization](Organization.md) (7 shared connections)
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) (6 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (6 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (6 shared connections)
- [SessionLocal](SessionLocal.md) (3 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (2 shared connections)
- [api/integrations.py](api-integrations.py.md) (2 shared connections)
- [sentinel.py](sentinel.py.md) (2 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [EvidenceLedger](EvidenceLedger.md) (2 shared connections)

## Source Files

- `app/services/connector_manager.py`
- `tests/aws_integration/test_evidence_pipeline.py`
- `tests/aws_integration/test_tenant_isolation.py`

## Audit Trail

- EXTRACTED: 151 (82%)
- INFERRED: 34 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*