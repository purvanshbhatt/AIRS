# activate_plan

> 14 nodes · cohesion 0.19

## Key Concepts

- **activate_plan()** (9 connections) — `app/api/billing.py`
- **get_capabilities()** (8 connections) — `app/api/billing.py`
- **get_billing_status()** (7 connections) — `app/api/billing.py`
- **billing_webhook()** (6 connections) — `app/api/billing.py`
- **Session** (4 connections)
- **PlanActivateRequest** (3 connections) — `app/api/billing.py`
- **User** (3 connections)
- **get** (2 connections)
- **post** (2 connections)
- **Request** (1 connections)
- **Directly activate a plan for the organization.** (1 connections) — `app/api/billing.py`
- **Handle Stripe webhook events. In production, this should verify the Stripe…** (1 connections) — `app/api/billing.py`
- **Return the organization's full entitlement map.** (1 connections) — `app/api/billing.py`
- **Return subscription details for the organization.** (1 connections) — `app/api/billing.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [User](User.md) (3 shared connections)
- [CheckoutService](CheckoutService.md) (2 shared connections)
- [Entitlement](Entitlement.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/api/billing.py`

## Audit Trail

- EXTRACTED: 26 (81%)
- INFERRED: 6 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*