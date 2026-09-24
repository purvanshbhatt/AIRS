# TestSecurityHubIngestion

> 22 nodes · cohesion 0.15

## Key Concepts

- **TestSecurityHubIngestion** (12 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **._make_connector()** (9 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **_run()** (7 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **test_security_hub_ingestion.py** (5 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_sync_empty_findings()** (4 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_sync_error_handling()** (4 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_sync_not_authenticated()** (4 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_sync_pagination()** (4 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_sync_returns_normalized_events()** (4 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_normalize_finding_payload_fields()** (3 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_normalize_finding_resource_extraction()** (3 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **.test_normalize_finding_severity_mapping()** (3 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **Tests for AWS Security Hub finding sync and normalization.** (2 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **Normalized finding contains all expected payload keys.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **Resource ARNs are extracted from finding.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **Multiple pages of findings are all collected.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **Run an async coroutine.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **API error during sync returns empty list, no crash.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **Sync with sample findings returns properly normalized RawEvents.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **Sync with no findings returns empty list.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **When hub_client is None, sync returns empty list without error.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`
- **All AWS severity labels map to expected ResilAI severity strings.** (1 connections) — `tests/aws_integration/test_security_hub_ingestion.py`

## Relationships

- [AWSSecurityHubConnector](AWSSecurityHubConnector.md) (4 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (1 shared connections)

## Source Files

- `tests/aws_integration/test_security_hub_ingestion.py`

## Audit Trail

- EXTRACTED: 38 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*