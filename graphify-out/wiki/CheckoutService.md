# CheckoutService

> 16 nodes · cohesion 0.16

## Key Concepts

- **CheckoutService** (14 connections) — `app/services/billing/checkout.py`
- **.handle_stripe_event()** (6 connections) — `app/services/billing/checkout.py`
- **._handle_payment_failed()** (4 connections) — `app/services/billing/checkout.py`
- **._handle_subscription_update()** (4 connections) — `app/services/billing/checkout.py`
- **.activate_plan_direct()** (3 connections) — `app/services/billing/checkout.py`
- **._handle_checkout_completed()** (3 connections) — `app/services/billing/checkout.py`
- **._handle_subscription_deleted()** (3 connections) — `app/services/billing/checkout.py`
- **.__init__()** (3 connections) — `app/services/billing/checkout.py`
- **Session** (1 connections)
- **Handle successful checkout — activate the subscription.** (1 connections) — `app/services/billing/checkout.py`
- **Handle subscription updates (plan changes, renewals).** (1 connections) — `app/services/billing/checkout.py`
- **Handle subscription cancellation.** (1 connections) — `app/services/billing/checkout.py`
- **Handle failed payment — set past_due status.** (1 connections) — `app/services/billing/checkout.py`
- **Manages plan selection, checkout, and activation.** (1 connections) — `app/services/billing/checkout.py`
- **Directly activate a plan for an organization. Used in staging/development and…** (1 connections) — `app/services/billing/checkout.py`
- **Process Stripe webhook events to synchronize subscription state. Supported…** (1 connections) — `app/services/billing/checkout.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [activate_plan](activate_plan.md) (2 shared connections)
- [Entitlement](Entitlement.md) (2 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [User](User.md) (1 shared connections)

## Source Files

- `app/services/billing/checkout.py`

## Audit Trail

- EXTRACTED: 25 (86%)
- INFERRED: 4 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*