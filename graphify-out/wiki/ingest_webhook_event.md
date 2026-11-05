# ingest_webhook_event

> 19 nodes · cohesion 0.12

## Key Concepts

- **ingest_webhook_event()** (8 connections) — `app/api/v1/governance_webhook.py`
- **SIEMEventWebhookPayload** (7 connections) — `app/schemas/telemetry_webhook.py`
- **_verify_auth()** (5 connections) — `app/api/v1/governance_webhook.py`
- **WebhookIngestionResponse** (5 connections) — `app/schemas/telemetry_webhook.py`
- **telemetry_webhook.py** (4 connections) — `app/schemas/telemetry_webhook.py`
- **.raw_telemetry_dump_must_not_be_empty()** (4 connections) — `app/schemas/telemetry_webhook.py`
- **.strip_and_validate_strings()** (3 connections) — `app/schemas/telemetry_webhook.py`
- **Session** (2 connections)
- **field_validator** (2 connections)
- **post** (1 connections)
- **Request** (1 connections)
- **Process a single SIEM webhook event via the Governance Engine.** (1 connections) — `app/api/v1/governance_webhook.py`
- **Dual-path M2M authentication: HMAC signature OR API key.** (1 connections) — `app/api/v1/governance_webhook.py`
- **Any** (1 connections)
- **Telemetry Webhook Schemas — Pydantic V2 type-safe contracts for SIEM ingestion.…** (1 connections) — `app/schemas/telemetry_webhook.py`
- **Inbound webhook payload from a Wazuh or Splunk SIEM integration. This is the…** (1 connections) — `app/schemas/telemetry_webhook.py`
- **Enforce non-empty telemetry payload. An empty dict provides no forensic…** (1 connections) — `app/schemas/telemetry_webhook.py`
- **Strip whitespace and reject blank strings.** (1 connections) — `app/schemas/telemetry_webhook.py`
- **Structured response from the telemetry webhook ingestion endpoint. status…** (1 connections) — `app/schemas/telemetry_webhook.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (5 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (1 shared connections)
- [services/integrations.py](services-integrations.py.md) (1 shared connections)

## Source Files

- `app/api/v1/governance_webhook.py`
- `app/schemas/telemetry_webhook.py`

## Audit Trail

- EXTRACTED: 27 (90%)
- INFERRED: 3 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*