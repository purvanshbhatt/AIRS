# verify_webhook_signature

> 4 nodes · cohesion 0.50

## Key Concepts

- **verify_webhook_signature()** (5 connections) — `app/api/v1/telemetry.py`
- **Session** (2 connections)
- **Request** (1 connections)
- **Verify the inbound request via HMAC signature OR API key. Security flow: 1. If…** (1 connections) — `app/api/v1/telemetry.py`

## Relationships

- [TelemetryVerificationService](TelemetryVerificationService.md) (2 shared connections)
- [services/integrations.py](services-integrations.py.md) (1 shared connections)

## Source Files

- `app/api/v1/telemetry.py`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*