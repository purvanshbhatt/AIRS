# NormalizedEvent

> 32 nodes · cohesion 0.10

## Key Concepts

- **NormalizedEvent** (40 connections) — `app/connectors/base.py`
- **MicrosoftConnector** (25 connections) — `app/connectors/microsoft.py`
- **connectors/test_evidence_pipeline.py** (19 connections) — `tests/connectors/test_evidence_pipeline.py`
- **test_microsoft_produces_user_evidence()** (9 connections) — `tests/connectors/test_evidence_pipeline.py`
- **test_wazuh_produces_device_evidence()** (9 connections) — `tests/connectors/test_evidence_pipeline.py`
- **.sync()** (8 connections) — `app/connectors/microsoft.py`
- **test_expired_evidence_ignored()** (7 connections) — `tests/connectors/test_evidence_pipeline.py`
- **test_organization_isolation_enforced()** (7 connections) — `tests/connectors/test_evidence_pipeline.py`
- **.authenticate()** (6 connections) — `app/connectors/microsoft.py`
- **asyncio** (6 connections)
- **.health_check()** (4 connections) — `app/connectors/microsoft.py`
- **._resolve_client_secret()** (4 connections) — `app/connectors/microsoft.py`
- **.validate_permissions()** (4 connections) — `app/connectors/microsoft.py`
- **test_connector_health_failure()** (4 connections) — `tests/connectors/test_evidence_pipeline.py`
- **load_secret_if_gcp()** (3 connections) — `app/connectors/microsoft.py`
- **.payload_hash()** (2 connections) — `app/connectors/base.py`
- **Connector-agnostic normalized telemetry event.** (1 connections) — `app/connectors/base.py`
- **Deterministic SHA-256 hash of the payload for deduplication.** (1 connections) — `app/connectors/base.py`
- **.__init__()** (1 connections) — `app/connectors/microsoft.py`
- **Connector** (1 connections)
- **Microsoft Graph security telemetry connector. Connects to the MS Graph API…** (1 connections) — `app/connectors/microsoft.py`
- **Helper to resolve client secret from config/GCP Secret Manager.** (1 connections) — `app/connectors/microsoft.py`
- **Authenticate via Client Credentials grant to Microsoft identity platform.** (1 connections) — `app/connectors/microsoft.py`
- **Fetch and normalize security telemetry from Intune, Entra ID, and Defender.** (1 connections) — `app/connectors/microsoft.py`
- **Verify Graph API endpoint connectivity.** (1 connections) — `app/connectors/microsoft.py`
- *... and 7 more nodes in this community*

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (22 shared connections)
- [EvidenceKind](EvidenceKind.md) (18 shared connections)
- [test_microsoft_connector.py](test_microsoft_connector.py.md) (9 shared connections)
- [WazuhConnector](WazuhConnector.md) (7 shared connections)
- [ConnectorManager](ConnectorManager.md) (6 shared connections)
- [DuoConnector](DuoConnector.md) (2 shared connections)
- [VeeamConnector](VeeamConnector.md) (2 shared connections)
- [WebhookConnector](WebhookConnector.md) (2 shared connections)
- [.safe_sync](safe_sync.md) (1 shared connections)
- [sentinel.py](sentinel.py.md) (1 shared connections)
- [Any](Any.md) (1 shared connections)
- [test_connector_registration](test_connector_registration.md) (1 shared connections)

## Source Files

- `app/connectors/base.py`
- `app/connectors/microsoft.py`
- `tests/connectors/test_evidence_pipeline.py`

## Audit Trail

- EXTRACTED: 91 (74%)
- INFERRED: 32 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*