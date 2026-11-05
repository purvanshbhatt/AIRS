# Connector

> 78 nodes · cohesion 0.04

## Key Concepts

- **Connector** (71 connections) — `app/models/connector.py`
- **ConnectorStatus** (40 connections) — `app/models/connector.py`
- **models/connector.py** (29 connections) — `app/models/connector.py`
- **connector_manager.py** (27 connections) — `app/services/connector_manager.py`
- **test_all_connectors_e2e.py** (23 connections) — `tests/test_all_connectors_e2e.py`
- **test_runtime_guardrails.py** (17 connections) — `tests/test_runtime_guardrails.py`
- **ConnectorAuthMethod** (14 connections) — `app/models/connector.py`
- **TestLiveAWSIntegration** (13 connections) — `tests/aws_integration/test_live_aws.py`
- **get_connector_class()** (12 connections) — `app/connectors/registry.py`
- **initialize_splunk_connector()** (12 connections) — `app/integrations/splunk/connector.py`
- **ingest_splunk_telemetry()** (11 connections) — `app/integrations/splunk/service.py`
- **configure_connector.py** (11 connections) — `tests/aws_integration/configure_connector.py`
- **test_live_aws.py** (10 connections) — `tests/aws_integration/test_live_aws.py`
- **service.py** (9 connections) — `app/integrations/splunk/service.py`
- **main()** (9 connections) — `tests/aws_integration/configure_connector.py`
- **ConnectorSyncResult** (8 connections) — `app/connectors/base.py`
- **splunk/connector.py** (8 connections) — `app/integrations/splunk/connector.py`
- **ConnectorSyncLog** (8 connections) — `app/models/connector.py`
- **test_audit_ledger_verification()** (8 connections) — `tests/test_runtime_guardrails.py`
- **.sync_connector()** (7 connections) — `app/services/connector_manager.py`
- **test_continuous_scoring_fresh_evidence()** (6 connections) — `tests/test_continuous_scoring.py`
- **.test_live_connector_manager_sync()** (5 connections) — `tests/aws_integration/test_live_aws.py`
- **test_connector_type_enum_completeness()** (5 connections) — `tests/test_all_connectors_e2e.py`
- **ConnectorManagerError** (4 connections) — `app/services/connector_manager.py`
- **test_all_connectors_health_check_non_blocking()** (4 connections) — `tests/test_all_connectors_e2e.py`
- *... and 53 more nodes in this community*

## Relationships

- [Organization](Organization.md) (32 shared connections)
- [ConnectorManager](ConnectorManager.md) (25 shared connections)
- [api/integrations.py](api-integrations.py.md) (20 shared connections)
- [app/db/database.py](app-db-database.py.md) (14 shared connections)
- [contracts.py](contracts.py.md) (14 shared connections)
- [splunk_staging_validation.py](splunk_staging_validation.py.md) (10 shared connections)
- [AWSSecurityHubConnector](AWSSecurityHubConnector.md) (10 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (9 shared connections)
- [get_user_org_id](get_user_org_id.md) (9 shared connections)
- [PilotService](PilotService.md) (7 shared connections)
- [BaseModel](BaseModel.md) (6 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (6 shared connections)

## Source Files

- `app/connectors/base.py`
- `app/connectors/registry.py`
- `app/integrations/splunk/connector.py`
- `app/integrations/splunk/service.py`
- `app/models/connector.py`
- `app/services/connector_manager.py`
- `tests/aws_integration/configure_connector.py`
- `tests/aws_integration/test_live_aws.py`
- `tests/test_all_connectors_e2e.py`
- `tests/test_continuous_scoring.py`
- `tests/test_runtime_guardrails.py`

## Audit Trail

- EXTRACTED: 265 (79%)
- INFERRED: 71 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*