# test_paywall_enforcement.py

> 18 nodes · cohesion 0.16

## Key Concepts

- **test_paywall_enforcement.py** (8 connections) — `tests/test_paywall_enforcement.py`
- **_auth_headers()** (7 connections) — `tests/test_paywall_enforcement.py`
- **TestPaywallEnforcement** (7 connections) — `tests/test_paywall_enforcement.py`
- **_mock_org()** (4 connections) — `tests/test_paywall_enforcement.py`
- **.test_billing_activate_works()** (4 connections) — `tests/test_paywall_enforcement.py`
- **.test_capabilities_endpoint_returns_plan()** (4 connections) — `tests/test_paywall_enforcement.py`
- **.test_402_returned_for_unpaid_api_key_create()** (3 connections) — `tests/test_paywall_enforcement.py`
- **.test_402_returned_for_unpaid_connector_create()** (3 connections) — `tests/test_paywall_enforcement.py`
- **.test_webhook_endpoint_accepts_events()** (3 connections) — `tests/test_paywall_enforcement.py`
- **Paywall enforcement integration tests. Verifies that endpoints correctly return…** (1 connections) — `tests/test_paywall_enforcement.py`
- **POST /api/orgs/{org_id}/api-keys should return 402 for unpaid org.** (1 connections) — `tests/test_paywall_enforcement.py`
- **POST /api/billing/webhook should process events.** (1 connections) — `tests/test_paywall_enforcement.py`
- **Return headers that bypass auth in dev mode.** (1 connections) — `tests/test_paywall_enforcement.py`
- **Create a mock org with subscription fields.** (1 connections) — `tests/test_paywall_enforcement.py`
- **Test that endpoints correctly enforce entitlements.** (1 connections) — `tests/test_paywall_enforcement.py`
- **GET /api/orgs/{org_id}/capabilities should return the entitlement map.** (1 connections) — `tests/test_paywall_enforcement.py`
- **POST /api/orgs/{org_id}/billing/activate should activate a plan.** (1 connections) — `tests/test_paywall_enforcement.py`
- **POST /api/v1/connectors should return 402 for unpaid org.** (1 connections) — `tests/test_paywall_enforcement.py`

## Relationships

- [Entitlement](Entitlement.md) (3 shared connections)
- [main.py](main.py.md) (1 shared connections)

## Source Files

- `tests/test_paywall_enforcement.py`

## Audit Trail

- EXTRACTED: 28 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*