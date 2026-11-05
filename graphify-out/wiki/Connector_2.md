# Connector

> God node · 71 connections · `app/models/connector.py`

**Community:** [Connector](Connector.md)

## Connections by Relation

### calls
- initialize_splunk_connector() `EXTRACTED`
- test_orchestrator_rejects_tampered_evidence() `EXTRACTED`
- test_audit_ledger_verification() `EXTRACTED`
- .seed_demo_clinic() `EXTRACTED`
- _create_test_connector() `EXTRACTED`
- .register_connector() `EXTRACTED`
- .test_live_connector_manager_sync() `EXTRACTED`
- _create_test_connector() `EXTRACTED`

### contains
- models/connector.py `EXTRACTED`

### imports
- models/__init__.py `EXTRACTED`
- [api/integrations.py](api-integrations.py.md) `EXTRACTED`
- v1/integrations.py `EXTRACTED`
- [connectors.py](connectors.py.md) `EXTRACTED`
- staging_real_customer_e2e.py `EXTRACTED`
- [sentinel.py](sentinel.py.md) `EXTRACTED`
- [test_microsoft_connector.py](test_microsoft_connector.py.md) `EXTRACTED`
- test_real_customer_e2e.py `EXTRACTED`
- readiness_engine.py `EXTRACTED`
- [test_evidence_integrity.py](test_evidence_integrity.py.md) `EXTRACTED`
- connector_manager.py `EXTRACTED`
- services/continuous_scoring.py `EXTRACTED`
- test_all_connectors_e2e.py `EXTRACTED`
- api/onboarding.py `EXTRACTED`
- v2/pilot.py `EXTRACTED`
- test_continuous_scoring.py `EXTRACTED`
- test_runtime_guardrails.py `EXTRACTED`
- [test_wazuh_connect.py](test_wazuh_connect.py.md) `EXTRACTED`
- trust_engine.py `EXTRACTED`
- test_demo_isolation.py `EXTRACTED`

### inherits
- Base `EXTRACTED`

### method
- .__repr__() `EXTRACTED`

### rationale_for
- External integration connector belonging to an organization. Design Rationale:… `EXTRACTED`

### uses
- [ConnectorManager](ConnectorManager.md) `INFERRED`
- ReadinessEngine `INFERRED`
- [ContinuousScoringEngine](ContinuousScoringEngine.md) `INFERRED`
- [PilotService](PilotService.md) `INFERRED`
- [ExplanationService](ExplanationService.md) `INFERRED`
- TrustEngine `INFERRED`
- run_e2e_validation() `INFERRED`
- run_splunk_query() `INFERRED`
- check_splunk_logging_health() `INFERRED`
- TelemetryConnectionManager `INFERRED`
- configure_splunk_hec() `INFERRED`
- get_onboarding_status() `INFERRED`
- configure_splunk() `INFERRED`
- get_siem_integration_status() `INFERRED`
- TestLiveAWSIntegration `INFERRED`
- pull_splunk_evidence() `INFERRED`
- ingest_splunk_telemetry() `INFERRED`
- CoverageEngine `INFERRED`
- check_microsoft_health() `INFERRED`
- trigger_microsoft_sync() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*