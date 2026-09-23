# AWSSecurityHubConnector

> 57 nodes · cohesion 0.05

## Key Concepts

- **AWSSecurityHubConnector** (43 connections) — `app/connectors/aws_security_hub.py`
- **TestNegativeCases** (12 connections) — `tests/aws_integration/test_negative_cases.py`
- **._make_connector()** (10 connections) — `tests/aws_integration/test_negative_cases.py`
- **TestDeterministicScoring** (8 connections) — `tests/aws_integration/test_deterministic_scoring.py`
- **_run()** (8 connections) — `tests/aws_integration/test_negative_cases.py`
- **._normalize_finding()** (6 connections) — `app/connectors/aws_security_hub.py`
- **test_negative_cases.py** (5 connections) — `tests/aws_integration/test_negative_cases.py`
- **.test_boto3_not_installed_graceful_degradation()** (4 connections) — `tests/aws_integration/test_negative_cases.py`
- **.test_insufficient_permissions()** (4 connections) — `tests/aws_integration/test_negative_cases.py`
- **.test_invalid_credentials_auth_fails()** (4 connections) — `tests/aws_integration/test_negative_cases.py`
- **.test_not_authenticated_validate_permissions()** (4 connections) — `tests/aws_integration/test_negative_cases.py`
- **.test_partial_sync_failure()** (4 connections) — `tests/aws_integration/test_negative_cases.py`
- **.test_security_hub_not_enabled()** (4 connections) — `tests/aws_integration/test_negative_cases.py`
- **.authenticate()** (3 connections) — `app/connectors/aws_security_hub.py`
- **.health_check()** (3 connections) — `app/connectors/aws_security_hub.py`
- **.sync()** (3 connections) — `app/connectors/aws_security_hub.py`
- **.validate_permissions()** (3 connections) — `app/connectors/aws_security_hub.py`
- **.test_control_mapping_not_implemented()** (3 connections) — `tests/aws_integration/test_deterministic_scoring.py`
- **.test_evidence_ingestion_preserves_payload()** (3 connections) — `tests/aws_integration/test_deterministic_scoring.py`
- **.test_live_security_hub_authentication()** (3 connections) — `tests/aws_integration/test_live_aws.py`
- **.test_live_security_hub_health()** (3 connections) — `tests/aws_integration/test_live_aws.py`
- **.test_live_security_hub_permissions()** (3 connections) — `tests/aws_integration/test_live_aws.py`
- **.test_live_security_hub_sync()** (3 connections) — `tests/aws_integration/test_live_aws.py`
- **.test_empty_payload_handling()** (3 connections) — `tests/aws_integration/test_negative_cases.py`
- **.test_malformed_finding_payload()** (3 connections) — `tests/aws_integration/test_negative_cases.py`
- *... and 32 more nodes in this community*

## Relationships

- [Connector](Connector.md) (10 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (10 shared connections)
- [TestSecurityHubIngestion](TestSecurityHubIngestion.md) (4 shared connections)
- [TestAWSConnection](TestAWSConnection.md) (3 shared connections)
- [run_e2e_test](run_e2e_test.md) (2 shared connections)
- [EvidenceAdapter](EvidenceAdapter.md) (1 shared connections)

## Source Files

- `app/connectors/aws_security_hub.py`
- `tests/aws_integration/test_deterministic_scoring.py`
- `tests/aws_integration/test_live_aws.py`
- `tests/aws_integration/test_negative_cases.py`

## Audit Trail

- EXTRACTED: 99 (90%)
- INFERRED: 11 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*