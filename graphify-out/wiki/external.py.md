# external.py

> 29 nodes · cohesion 0.10

## Key Concepts

- **external.py** (18 connections) — `app/api/external.py`
- **ApiKey** (14 connections) — `app/models/api_key.py`
- **api_key_auth.py** (11 connections) — `app/core/api_key_auth.py`
- **receive_telemetry_webhook()** (8 connections) — `app/api/external.py`
- **get_latest_score_for_external()** (7 connections) — `app/api/external.py`
- **api_key.py** (7 connections) — `app/models/api_key.py`
- **get_api_key_dependency()** (6 connections) — `app/core/api_key_auth.py`
- **TelemetryPayloadSchema** (6 connections) — `app/core/security/webhooks.py`
- **webhooks.py** (5 connections) — `app/core/security/webhooks.py`
- **TelemetryInterceptor** (4 connections) — `app/core/security/webhooks.py`
- **.__call__()** (3 connections) — `app/core/security/webhooks.py`
- **Request** (2 connections)
- **Session** (2 connections)
- **limit** (2 connections)
- **get** (1 connections)
- **post** (1 connections)
- **External integration endpoints (API key secured, rate-limited).** (1 connections) — `app/api/external.py`
- **Ingest external telemetry events. Strictly protected by TelemetryInterceptor…** (1 connections) — `app/api/external.py`
- **API key authentication dependencies for external integrations.** (1 connections) — `app/core/api_key_auth.py`
- **Create an API key dependency with optional scope enforcement.** (1 connections) — `app/core/api_key_auth.py`
- **Config** (1 connections) — `app/core/security/webhooks.py`
- **Request** (1 connections)
- **Webhook interceptor for incoming telemetry payloads. Provides strict…** (1 connections) — `app/core/security/webhooks.py`
- **FastAPI Dependency that acts as a runtime protection guardrail for incoming…** (1 connections) — `app/core/security/webhooks.py`
- **.__init__()** (1 connections) — `app/core/security/webhooks.py`
- *... and 4 more nodes in this community*

## Relationships

- [services/integrations.py](services-integrations.py.md) (11 shared connections)
- [app/db/database.py](app-db-database.py.md) (9 shared connections)
- [BaseModel](BaseModel.md) (3 shared connections)
- [Organization](Organization.md) (3 shared connections)
- [get_user_org_id](get_user_org_id.md) (2 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (2 shared connections)

## Source Files

- `app/api/external.py`
- `app/core/api_key_auth.py`
- `app/core/security/webhooks.py`
- `app/models/api_key.py`

## Audit Trail

- EXTRACTED: 65 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*