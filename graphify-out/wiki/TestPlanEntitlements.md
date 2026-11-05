# TestPlanEntitlements

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestPlanEntitlements** (8 connections) — `tests/test_entitlements_service.py`
- **.test_plans_are_cumulative()** (2 connections) — `tests/test_entitlements_service.py`
- **Each higher plan is a strict superset of the lower plan.** (1 connections) — `tests/test_entitlements_service.py`
- **Verify entitlement mapping integrity.** (1 connections) — `tests/test_entitlements_service.py`
- **.test_design_partner_includes_free_and_core_paid()** (1 connections) — `tests/test_entitlements_service.py`
- **.test_enterprise_includes_everything()** (1 connections) — `tests/test_entitlements_service.py`
- **.test_free_plan_has_only_base_entitlements()** (1 connections) — `tests/test_entitlements_service.py`
- **.test_growth_includes_api_keys_and_webhooks()** (1 connections) — `tests/test_entitlements_service.py`

## Relationships

- [_create_service](_create_service.md) (1 shared connections)
- [Entitlement](Entitlement.md) (1 shared connections)

## Source Files

- `tests/test_entitlements_service.py`

## Audit Trail

- EXTRACTED: 8 (89%)
- INFERRED: 1 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*