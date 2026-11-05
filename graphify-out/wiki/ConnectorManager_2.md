# ConnectorManager

> God node · 77 connections · `app/services/connector_manager.py`

**Community:** [ConnectorManager](ConnectorManager.md)

## Connections by Relation

### calls
- run_e2e_validation() `EXTRACTED`
- ingest_splunk_telemetry() `EXTRACTED`
- main() `EXTRACTED`
- .test_org_a_cannot_access_org_b_telemetry() `EXTRACTED`
- .test_events_create_telemetry_records() `EXTRACTED`
- .test_no_credentials_in_telemetry_payload() `EXTRACTED`
- .test_org_id_scoping() `EXTRACTED`
- .test_telemetry_deduplication() `EXTRACTED`
- .test_live_connector_manager_sync() `EXTRACTED`
- .test_connector_manager_enforces_org_scope() `EXTRACTED`
- .test_org_a_cannot_access_org_b_connector() `EXTRACTED`
- ._monitor_health() `EXTRACTED`
- ._sync_connectors() `EXTRACTED`
- test_register_and_retrieve_all_connectors() `EXTRACTED`
- .test_list_connectors_scoped_to_org() `EXTRACTED`
- .test_register_splunk_connector() `EXTRACTED`
- .test_connector_manager_enforces_tenant_isolation() `EXTRACTED`

### contains
- connector_manager.py `EXTRACTED`

### imports
- [api/integrations.py](api-integrations.py.md) `EXTRACTED`
- v1/integrations.py `EXTRACTED`
- [connectors.py](connectors.py.md) `EXTRACTED`
- staging_real_customer_e2e.py `EXTRACTED`
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) `EXTRACTED`
- [sentinel.py](sentinel.py.md) `EXTRACTED`
- test_real_customer_e2e.py `EXTRACTED`
- test_all_connectors_e2e.py `EXTRACTED`
- scheduler.py `EXTRACTED`
- aws_integration/test_tenant_isolation.py `EXTRACTED`
- configure_connector.py `EXTRACTED`
- aws_integration/test_evidence_pipeline.py `EXTRACTED`
- test_live_aws.py `EXTRACTED`
- service.py `EXTRACTED`

### method
- ._ingest_into_evidence_registry() `EXTRACTED`
- ._ensure_adapter_registered() `EXTRACTED`
- .sync_connector() `EXTRACTED`
- ._decrypt_credentials() `EXTRACTED`
- ._ingest_events() `EXTRACTED`
- .register_connector() `EXTRACTED`
- .health_check() `EXTRACTED`
- .validate_permissions() `EXTRACTED`
- .get_connector() `EXTRACTED`
- ._encrypt_credentials() `EXTRACTED`
- .update_connector() `EXTRACTED`
- .list_connectors() `EXTRACTED`
- .get_sync_history() `EXTRACTED`
- .deactivate_connector() `EXTRACTED`
- .__init__() `EXTRACTED`

### rationale_for
- Organization-scoped connector lifecycle management. Handles registration, sync… `EXTRACTED`

### uses
- [Connector](Connector.md) `INFERRED`
- [TelemetryEvent](TelemetryEvent.md) `INFERRED`
- ConnectorStatus `INFERRED`
- WazuhClient `INFERRED`
- run_splunk_query() `INFERRED`
- check_splunk_logging_health() `INFERRED`
- test_real_customer_e2e_lifecycle() `INFERRED`
- TestLiveAWSIntegration `INFERRED`
- pull_splunk_evidence() `INFERRED`
- connect_wazuh() `INFERRED`
- check_microsoft_health() `INFERRED`
- trigger_microsoft_sync() `INFERRED`
- trigger_sync() `INFERRED`
- TaskScheduler `INFERRED`
- TestEvidencePipeline `INFERRED`
- check_health() `INFERRED`
- create_connector() `INFERRED`
- update_connector() `INFERRED`
- TestTenantIsolation `INFERRED`
- trigger_splunk_sync() `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*