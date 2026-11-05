# test_integrations.py

> 17 nodes · cohesion 0.18

## Key Concepts

- **test_integrations.py** (16 connections) — `tests/test_integrations.py`
- **Webhook** (10 connections) — `app/models/webhook.py`
- **models/webhook.py** (6 connections) — `app/models/webhook.py`
- **_create_scored_assessment()** (5 connections) — `tests/test_integrations.py`
- **_submit_full_answers()** (4 connections) — `tests/test_integrations.py`
- **test_dispatch_assessment_scored_webhooks_retries()** (4 connections) — `tests/test_integrations.py`
- **test_compute_score_enqueues_webhook_dispatch()** (2 connections) — `tests/test_integrations.py`
- **test_external_latest_score_rejects_insufficient_scope()** (2 connections) — `tests/test_integrations.py`
- **test_external_latest_score_requires_api_key()** (2 connections) — `tests/test_integrations.py`
- **test_external_latest_score_with_valid_api_key()** (2 connections) — `tests/test_integrations.py`
- **test_org_audit_endpoint_records_core_events()** (2 connections) — `tests/test_integrations.py`
- **Base** (1 connections)
- **Webhook model for outbound event delivery.** (1 connections) — `app/models/webhook.py`
- **Organization-scoped webhook destinations.** (1 connections) — `app/models/webhook.py`
- **.__repr__()** (1 connections) — `app/models/webhook.py`
- **test_mock_splunk_seed_and_list_external_findings()** (1 connections) — `tests/test_integrations.py`
- **test_webhook_url_test_endpoint_sends_payload()** (1 connections) — `tests/test_integrations.py`

## Relationships

- [Organization](Organization.md) (6 shared connections)
- [services/integrations.py](services-integrations.py.md) (4 shared connections)
- [User](User.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `app/models/webhook.py`
- `tests/test_integrations.py`

## Audit Trail

- EXTRACTED: 37 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*