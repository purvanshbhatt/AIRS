# EvidenceAdapter

> 23 nodes · cohesion 0.13

## Key Concepts

- **EvidenceAdapter** (24 connections) — `app/services/evidence/base_adapter.py`
- **base_adapter.py** (17 connections) — `app/services/evidence/base_adapter.py`
- **evidence/adapters/splunk.py** (12 connections) — `app/services/evidence/adapters/splunk.py`
- **adapters/wazuh.py** (11 connections) — `app/services/evidence/adapters/wazuh.py`
- **services/evidence/__init__.py** (11 connections) — `app/services/evidence/__init__.py`
- **adapters/aws_security_hub.py** (9 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **evidence/registry.py** (9 connections) — `app/services/evidence/registry.py`
- **ManualUploadAdapter** (6 connections) — `app/services/evidence/base_adapter.py`
- **WebhookEvidenceAdapter** (6 connections) — `app/services/evidence/base_adapter.py`
- **evidence/adapters/__init__.py** (4 connections) — `app/services/evidence/adapters/__init__.py`
- **.fetch_evidence()** (4 connections) — `app/services/evidence/base_adapter.py`
- **.connector_name()** (2 connections) — `app/services/evidence/base_adapter.py`
- **.supported_mime_types()** (2 connections) — `app/services/evidence/base_adapter.py`
- **datetime** (2 connections)
- **EvidenceAdapter base class — vendor-agnostic telemetry ingestion. Per ADR-009,…** (1 connections) — `app/services/evidence/base_adapter.py`
- **Stable identifier (e.g. 'splunk', 'wazuh', 'aws_ssminventory').** (1 connections) — `app/services/evidence/base_adapter.py`
- **Fetch evidence from the underlying vendor. Implementations must return…** (1 connections) — `app/services/evidence/base_adapter.py`
- **Conceptual interface for ingesting generic JSON webhooks. Allows the pipeline…** (1 connections) — `app/services/evidence/base_adapter.py`
- **Conceptual interface for manual evidence uploads. Supports the ingestion of…** (1 connections) — `app/services/evidence/base_adapter.py`
- **List of MIME types this adapter can process (e.g. 'application/pdf',…** (1 connections) — `app/services/evidence/base_adapter.py`
- **Base class for vendor-agnostic telemetry adapters. Subclasses MUST override all…** (1 connections) — `app/services/evidence/base_adapter.py`
- **Transport-Agnostic Evidence Collection Layer. Public symbols re-exported so…** (1 connections) — `app/services/evidence/__init__.py`
- **EvidenceRegistry — vendor-agnostic connector resolution. Adapters register…** (1 connections) — `app/services/evidence/registry.py`

## Relationships

- [EvidenceRecord](EvidenceRecord.md) (10 shared connections)
- [AdapterHealth](AdapterHealth.md) (9 shared connections)
- [SplunkAdapter](SplunkAdapter.md) (8 shared connections)
- [WazuhAdapter](WazuhAdapter.md) (8 shared connections)
- [test_connectors_confidence_api.py](test_connectors_confidence_api.py.md) (8 shared connections)
- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [AWSSecurityHubAdapter](AWSSecurityHubAdapter.md) (3 shared connections)
- [EvidenceRegistry](EvidenceRegistry.md) (3 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (2 shared connections)
- [WazuhConfig](WazuhConfig.md) (2 shared connections)
- [AWSSecurityHubConnector](AWSSecurityHubConnector.md) (1 shared connections)
- [SplunkConnector](SplunkConnector.md) (1 shared connections)

## Source Files

- `app/services/evidence/__init__.py`
- `app/services/evidence/adapters/__init__.py`
- `app/services/evidence/adapters/aws_security_hub.py`
- `app/services/evidence/adapters/splunk.py`
- `app/services/evidence/adapters/wazuh.py`
- `app/services/evidence/base_adapter.py`
- `app/services/evidence/registry.py`

## Audit Trail

- EXTRACTED: 87 (93%)
- INFERRED: 7 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*