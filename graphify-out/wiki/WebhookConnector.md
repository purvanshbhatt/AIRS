# WebhookConnector

> 12 nodes · cohesion 0.17

## Key Concepts

- **WebhookConnector** (16 connections) — `app/connectors/webhook.py`
- **.health_check()** (3 connections) — `app/connectors/webhook.py`
- **.sync()** (3 connections) — `app/connectors/webhook.py`
- **.validate_permissions()** (3 connections) — `app/connectors/webhook.py`
- **.authenticate()** (2 connections) — `app/connectors/webhook.py`
- **Connector** (1 connections)
- **Custom Webhook / Generic API connector for MSP telemetry ingestion.** (1 connections) — `app/connectors/webhook.py`
- **Webhooks receive payloads actively; registration confirms readiness.** (1 connections) — `app/connectors/webhook.py`
- **Webhooks are push-based; pull sync returns active status heartbeat.** (1 connections) — `app/connectors/webhook.py`
- **Health check verifies internal readiness to receive webhook events.** (1 connections) — `app/connectors/webhook.py`
- **Permissions are valid upon connector registration.** (1 connections) — `app/connectors/webhook.py`
- **.__init__()** (1 connections) — `app/connectors/webhook.py`

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (8 shared connections)
- [Connector](Connector.md) (2 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (2 shared connections)

## Source Files

- `app/connectors/webhook.py`

## Audit Trail

- EXTRACTED: 17 (74%)
- INFERRED: 6 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*