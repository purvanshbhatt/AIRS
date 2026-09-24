# Entitlement

> 26 nodes · cohesion 0.12

## Key Concepts

- **Entitlement** (30 connections) — `app/services/billing/entitlements.py`
- **EntitlementService** (21 connections) — `app/services/billing/entitlements.py`
- **core/entitlements.py** (19 connections) — `app/core/entitlements.py`
- **billing/entitlements.py** (17 connections) — `app/services/billing/entitlements.py`
- **require_entitlement()** (10 connections) — `app/core/entitlements.py`
- **.get_capabilities()** (5 connections) — `app/services/billing/entitlements.py`
- **.get_effective_plan()** (5 connections) — `app/services/billing/entitlements.py`
- **._get_org()** (5 connections) — `app/services/billing/entitlements.py`
- **.activate_plan()** (4 connections) — `app/services/billing/entitlements.py`
- **.deactivate()** (4 connections) — `app/services/billing/entitlements.py`
- **.has()** (4 connections) — `app/services/billing/entitlements.py`
- **billing/__init__.py** (3 connections) — `app/services/billing/__init__.py`
- **.__init__()** (2 connections) — `app/services/billing/entitlements.py`
- **Entitlement enforcement dependencies for FastAPI routes. Usage: from…** (1 connections) — `app/core/entitlements.py`
- **FastAPI dependency factory that gates access by entitlement. Returns HTTP 402…** (1 connections) — `app/core/entitlements.py`
- **Any** (1 connections)
- **Session** (1 connections)
- **str** (1 connections)
- **ResilAI Entitlement Engine. Defines subscription plans, their entitlements, and…** (1 connections) — `app/services/billing/entitlements.py`
- **Return the plan the org is effectively on right now. If subscription_status is…** (1 connections) — `app/services/billing/entitlements.py`
- **Check if the organization has a specific entitlement.** (1 connections) — `app/services/billing/entitlements.py`
- **Return the full capability map for an organization. This is the payload…** (1 connections) — `app/services/billing/entitlements.py`
- **Activate or change a subscription plan for an organization. Called by checkout…** (1 connections) — `app/services/billing/entitlements.py`
- **Deactivate an organization's subscription (e.g. on cancellation).** (1 connections) — `app/services/billing/entitlements.py`
- **Capabilities that can be gated by subscription plan.** (1 connections) — `app/services/billing/entitlements.py`
- *... and 1 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (14 shared connections)
- [agent_audits.py](agent_audits.py.md) (8 shared connections)
- [api/integrations.py](api-integrations.py.md) (8 shared connections)
- [organizations.py](organizations.py.md) (6 shared connections)
- [connectors.py](connectors.py.md) (6 shared connections)
- [_create_service](_create_service.md) (6 shared connections)
- [telemetry_events.py](telemetry_events.py.md) (5 shared connections)
- [test_paywall_enforcement.py](test_paywall_enforcement.py.md) (3 shared connections)
- [User](User.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)
- [CheckoutService](CheckoutService.md) (2 shared connections)
- [get_user_org_id](get_user_org_id.md) (1 shared connections)

## Source Files

- `app/core/entitlements.py`
- `app/services/billing/__init__.py`
- `app/services/billing/entitlements.py`

## Audit Trail

- EXTRACTED: 84 (81%)
- INFERRED: 20 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*