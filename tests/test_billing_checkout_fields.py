"""
Billing checkout field tests — invoice-friendly Stripe Checkout payload,
founding-seat cap, billing portal and the public billing config endpoint.
"""
import os

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

import pytest
from unittest.mock import patch

from app.models.organization import Organization
from app.services.billing.checkout import CheckoutService
from app.services.billing.entitlements import EntitlementService

ORG_ID = "test-org-123"  # provisioned by client_with_org


def _svc(db):
    return CheckoutService(db)


def test_checkout_payload_collects_invoice_fields(db_session, client_with_org):
    with patch("app.core.config.settings.STRIPE_PRICE_DESIGN_PARTNER", "price_dp"), \
         patch("app.core.config.settings.STRIPE_TRIAL_DAYS", 14), \
         patch("app.core.config.settings.STRIPE_AUTOMATIC_TAX", False):
        payload = _svc(db_session).build_checkout_payload(
            org_id=ORG_ID, plan="founding-sysadmin",
            success_url="https://app/x", cancel_url="https://app/c",
            customer_email="admin@clinic.test",
        )
    assert payload["mode"] == "subscription"
    assert payload["line_items[0][price]"] == "price_dp"
    assert payload["billing_address_collection"] == "required"
    assert payload["tax_id_collection[enabled]"] == "true"
    assert payload["allow_promotion_codes"] == "true"
    assert payload["customer_creation"] == "always"
    assert payload["customer_email"] == "admin@clinic.test"
    assert payload["subscription_data[trial_period_days]"] == "14"
    assert payload["payment_method_collection"] == "if_required"
    assert payload["subscription_data[metadata][org_id]"] == ORG_ID
    assert payload["subscription_data[metadata][plan]"] == "founding-sysadmin"
    assert "automatic_tax[enabled]" not in payload
    assert "{CHECKOUT_SESSION_ID}" in payload["success_url"]


def test_checkout_payload_reuses_customer_and_tax(db_session, client_with_org):
    with patch("app.core.config.settings.STRIPE_PRICE_GROWTH", "price_growth"), \
         patch("app.core.config.settings.STRIPE_TRIAL_DAYS", 0), \
         patch("app.core.config.settings.STRIPE_AUTOMATIC_TAX", True):
        payload = _svc(db_session).build_checkout_payload(
            org_id=ORG_ID, plan="growth",
            success_url="https://app/x?session_id={CHECKOUT_SESSION_ID}", cancel_url="https://app/c",
            customer_email="admin@clinic.test", customer_id="cus_123",
        )
    assert payload["customer"] == "cus_123"
    assert payload["customer_update[name]"] == "auto"
    assert payload["customer_update[address]"] == "auto"
    assert "customer_creation" not in payload and "customer_email" not in payload
    assert "subscription_data[trial_period_days]" not in payload
    assert payload["automatic_tax[enabled]"] == "true"


def test_checkout_payload_requires_price_id_without_fallback(db_session, client_with_org):
    with patch("app.core.config.settings.STRIPE_PRICE_GROWTH", None):
        with pytest.raises(ValueError):
            _svc(db_session).build_checkout_payload(
                org_id=ORG_ID, plan="growth", success_url="https://a", cancel_url="https://b",
                allow_price_data_fallback=False,
            )
        payload = _svc(db_session).build_checkout_payload(
            org_id=ORG_ID, plan="growth", success_url="https://a", cancel_url="https://b",
            allow_price_data_fallback=True,
        )
    assert payload["line_items[0][price_data][unit_amount]"] == "39900"


def test_founding_seats_counted_from_db_and_capped(db_session, client_with_org):
    for i in range(3):
        db_session.add(Organization(
            id=f"founder-{i}", name=f"Founder {i}", owner_uid=f"u{i}",
            subscription_plan="founding-sysadmin", subscription_status="active",
        ))
    db_session.add(Organization(id="lapsed", name="Lapsed", owner_uid="u9",
                                subscription_plan="founding-sysadmin", subscription_status="canceled"))
    db_session.commit()

    seats = EntitlementService(db_session).founding_seats()
    assert seats["claimed"] == 3 and seats["sold_out"] is False

    with patch("app.core.config.settings.FOUNDING_SEATS_TOTAL", 3):
        seats = EntitlementService(db_session).founding_seats()
        assert seats["sold_out"] is True and seats["remaining"] == 0

    resp = client_with_org.get("/api/billing/public-config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["founding_seats"]["claimed"] == 3
    assert body["founding_seats"]["total"] == 50
    assert isinstance(body["trial_days"], int)


@pytest.mark.asyncio
async def test_checkout_refuses_when_sold_out_or_already_subscribed(db_session, client_with_org):
    svc = _svc(db_session)
    with patch("app.core.config.settings.FOUNDING_SEATS_TOTAL", 0):
        result = await svc.create_checkout_session(ORG_ID, "founding-sysadmin", "https://a", "https://b")
    assert result["success"] is False and result["code"] == "FOUNDING_SOLD_OUT"

    org = db_session.query(Organization).filter(Organization.id == ORG_ID).first()
    org.subscription_plan = "growth"
    org.subscription_status = "active"
    org.subscription_id = "sub_1"
    db_session.commit()
    result = await svc.create_checkout_session(ORG_ID, "growth", "https://a", "https://b")
    assert result["success"] is False and result["code"] == "SUBSCRIPTION_EXISTS"


def test_portal_requires_customer(db_session, client_with_org):
    resp = client_with_org.post(f"/api/orgs/{ORG_ID}/billing/portal", json={"return_url": "https://app/settings"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "NO_CUSTOMER"


def test_past_due_keeps_entitlements_during_grace(db_session, client_with_org):
    org = db_session.query(Organization).filter(Organization.id == ORG_ID).first()
    org.subscription_plan = "growth"
    org.subscription_status = "past_due"
    db_session.commit()
    caps = EntitlementService(db_session).get_capabilities(ORG_ID)
    assert caps["status"] == "past_due"
    assert caps["entitlements"]["connectors_manage"] is True
