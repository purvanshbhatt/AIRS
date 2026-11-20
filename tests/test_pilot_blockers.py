"""
Regression proofs for defects found while preparing the first pilot.

* An auditor link can only be revoked by the owner of the organisation it was
  issued for.
* Connecting Microsoft 365 does not make reports say email security is
  monitored: no check looks at email yet.
"""
from types import SimpleNamespace

from app.models.organization import Organization
from app.services import auditor_view
from app.services.clinic_engine.v2 import coverage_engine

OWN_ORG = "test-org-123"  # provisioned by the client_with_org fixture
REVOKE = "/api/governance/orgs/{org}/auditor-link"


# ---------------------------------------------------------------------------
# Auditor links
# ---------------------------------------------------------------------------

def test_revoke_ignores_a_token_issued_for_another_organisation():
    link = auditor_view.create_auditor_link("org-a", "Org A", "user-a")

    assert auditor_view.revoke_token(link["token"], org_id="org-b") is False
    assert auditor_view.validate_token(link["token"]) is not None

    assert auditor_view.revoke_token(link["token"], org_id="org-a") is True
    assert auditor_view.validate_token(link["token"]) is None


def test_revoke_endpoint_needs_ownership_of_the_organisation(db_session, client_with_org):
    db_session.add(Organization(id="someone-elses-org", name="Other Practice", owner_uid="another-user"))
    db_session.commit()
    link = auditor_view.create_auditor_link("someone-elses-org", "Other Practice", "another-user")

    # Not the caller's organisation.
    resp = client_with_org.delete(REVOKE.format(org="someone-elses-org"), params={"token": link["token"]})
    assert resp.status_code == 404, resp.text

    # The caller's own organisation, but a token issued for a different one.
    resp = client_with_org.delete(REVOKE.format(org=OWN_ORG), params={"token": link["token"]})
    assert resp.status_code == 404, resp.text

    assert auditor_view.validate_token(link["token"]) is not None


def test_owner_can_revoke_their_own_link(db_session, client_with_org):
    link = auditor_view.create_auditor_link(OWN_ORG, "Provisioned Org", "owner")

    resp = client_with_org.delete(REVOKE.format(org=OWN_ORG), params={"token": link["token"]})

    assert resp.status_code == 200, resp.text
    assert auditor_view.validate_token(link["token"]) is None


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def _coverage_with(monkeypatch, db_session, *connector_types):
    monkeypatch.setattr(
        coverage_engine,
        "connected_connectors",
        lambda db, org_id: [SimpleNamespace(connector_type=t) for t in connector_types],
    )
    return coverage_engine.CoverageEngine(db_session).assess_coverage("any-org")


def test_microsoft_365_alone_is_not_reported_as_covering_email(monkeypatch, db_session):
    report = _coverage_with(monkeypatch, db_session, "microsoft")

    monitored = {a.area for a in report.monitored}
    not_monitored = {a.area for a in report.not_monitored}
    assert "Email Security" in not_monitored
    assert "Email Security" not in monitored
    # What Microsoft 365 really feeds is still counted.
    assert {"Users & Identities", "Multi-Factor Authentication", "Devices & Endpoints"} <= monitored


def test_no_existing_connector_claims_email_coverage(monkeypatch, db_session):
    every_type = ["microsoft", "aws", "aws_security_hub", "veeam", "duo", "wazuh", "splunk", "webhook"]
    report = _coverage_with(monkeypatch, db_session, *every_type)

    assert "Email Security" in {a.area for a in report.not_monitored}
