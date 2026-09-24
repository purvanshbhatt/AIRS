# test_production_org_lifecycle.py

> 79 nodes · cohesion 0.03

## Key Concepts

- **test_production_org_lifecycle.py** (36 connections) — `tests/test_production_org_lifecycle.py`
- **create_test_org()** (21 connections) — `tests/test_production_org_lifecycle.py`
- **patch** (13 connections)
- **TestTenantIsolation** (8 connections) — `tests/test_production_org_lifecycle.py`
- **TestSplunkConnectorLifecycle** (7 connections) — `tests/test_production_org_lifecycle.py`
- **create_test_telemetry()** (6 connections) — `tests/test_production_org_lifecycle.py`
- **.test_readiness_deterministic_after_cold_start()** (6 connections) — `tests/test_production_org_lifecycle.py`
- **.test_readiness_score_is_llm_independent()** (5 connections) — `tests/test_production_org_lifecycle.py`
- **TestNoDemoSeedInProduction** (5 connections) — `tests/test_production_org_lifecycle.py`
- **TestOrganizationLifecycle** (5 connections) — `tests/test_production_org_lifecycle.py`
- **OrgMode** (4 connections) — `app/services/clinic_engine/v2/pilot.py`
- **TestDeterministicScoring** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_scoring_is_deterministic()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **TestLLMIsolation** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_readiness_endpoint_does_not_seed_demo_for_real_org()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **TestOrgIdValidation** (4 connections) — `tests/test_production_org_lifecycle.py`
- **TestRealOrgReadiness** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_new_real_org_gets_no_demo_telemetry()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_persisted_telemetry_consumed_by_readiness()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_list_connectors_scoped_to_org()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_register_splunk_connector()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_telemetry_creates_evidence_events()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_connector_manager_enforces_tenant_isolation()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_org_service_enforces_tenant_isolation()** (4 connections) — `tests/test_production_org_lifecycle.py`
- **.test_telemetry_isolation()** (4 connections) — `tests/test_production_org_lifecycle.py`
- *... and 54 more nodes in this community*

## Relationships

- [Organization](Organization.md) (8 shared connections)
- [ConnectorManager](ConnectorManager.md) (6 shared connections)
- [contracts.py](contracts.py.md) (6 shared connections)
- [get_firestore_client](get_firestore_client.md) (5 shared connections)
- [PilotService](PilotService.md) (4 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [ClinicMoment](ClinicMoment.md) (3 shared connections)
- [connectors.py](connectors.py.md) (2 shared connections)
- [schema.py](schema.py.md) (2 shared connections)
- [router.py](router.py.md) (1 shared connections)
- [main.py](main.py.md) (1 shared connections)

## Source Files

- `app/services/clinic_engine/v2/pilot.py`
- `tests/test_production_org_lifecycle.py`

## Audit Trail

- EXTRACTED: 144 (95%)
- INFERRED: 7 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*