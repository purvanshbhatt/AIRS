"""
Regional framework applicability: EU AI Act, Gulf states and other regions.

The rules are deterministic. A framework is listed because of what the
organisation says about itself (data it handles, AI use, where it operates),
never because of a guess, and a US-only law is not shown to an organisation
that operates elsewhere.
"""
import json
from types import SimpleNamespace

import pytest

from app.models.organization import Organization
from app.services.governance.compliance_engine import (
    GULF_STATES,
    get_applicable_frameworks,
    normalise_regions,
)
from app.services.governance.validation_engine import compute_compliance

OWN_ORG = "test-org-123"  # provisioned by the client_with_org fixture
EU_AI_ACT = "EU AI Act (Regulation (EU) 2024/1689)"

GULF_PRIVACY_LAWS = {
    "AE": "UAE PDPL (Federal Decree-Law No. 45 of 2021)",
    "SA": "Saudi PDPL (Personal Data Protection Law)",
    "QA": "Qatar PDPPL (Law No. 13 of 2016)",
    "BH": "Bahrain PDPL (Law No. 30 of 2018)",
    "KW": "Kuwait CITRA Data Privacy Protection Regulation",
    "OM": "Oman PDPL (Royal Decree 6/2022)",
}


def _org(regions=None, country=None, **flags):
    base = dict(
        id="org-1",
        industry=None,
        country=country,
        geo_regions=json.dumps(regions) if regions is not None else None,
        processes_pii=False,
        processes_phi=False,
        processes_cardholder_data=False,
        handles_dod_data=False,
        uses_ai_in_production=False,
        government_contractor=False,
        financial_services=False,
    )
    base.update(flags)
    return SimpleNamespace(**base)


def _names(org):
    return [f.framework for f in get_applicable_frameworks(org)]


def _get(org, name):
    return next(f for f in get_applicable_frameworks(org) if f.framework == name)


# ---------------------------------------------------------------------------
# EU AI Act
# ---------------------------------------------------------------------------

def test_ai_use_in_the_eu_lists_the_eu_ai_act():
    act = _get(_org(["EU"], uses_ai_in_production=True), EU_AI_ACT)

    assert act.mandatory is True
    assert act.jurisdiction == "European Union"
    assert act.reference_url == "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
    # It says what the product does not do, so nobody reads it as a conformity claim.
    assert "does not verify" in act.evidence_note
    assert "Article 15" in act.evidence_note


def test_eu_ai_act_needs_both_ai_use_and_an_eu_presence():
    assert EU_AI_ACT not in _names(_org(["EU"]))
    assert EU_AI_ACT not in _names(_org(["US"], uses_ai_in_production=True))
    assert EU_AI_ACT not in _names(_org(uses_ai_in_production=True))
    # The existing AI framework is still listed for everyone who uses AI.
    assert "NIST AI RMF" in _names(_org(["US"], uses_ai_in_production=True))


def test_a_member_state_given_as_the_country_counts_as_the_eu():
    names = _names(_org(country="Germany", uses_ai_in_production=True, processes_pii=True))

    assert EU_AI_ACT in names
    assert "GDPR" in names
    assert "NIST Privacy Framework" not in names


def test_eu_adds_nis2_as_advisory_and_dora_only_for_finance():
    org = _org(["EU"])
    nis2 = _get(org, "NIS2 Directive (EU) 2022/2555")
    assert nis2.mandatory is False
    assert "multi-factor authentication" in nis2.evidence_note
    assert "DORA (Regulation (EU) 2022/2554)" not in _names(org)

    finance = _org(["EU"], financial_services=True)
    assert _get(finance, "DORA (Regulation (EU) 2022/2554)").mandatory is True
    # FFIEC is a US examination regime.
    assert "FFIEC IT Handbook" not in _names(finance)
    assert "FFIEC IT Handbook" in _names(_org(["US", "EU"], financial_services=True))


# ---------------------------------------------------------------------------
# Gulf states
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("code,law", sorted(GULF_PRIVACY_LAWS.items()))
def test_each_gulf_state_lists_its_own_data_protection_law(code, law):
    listed = _get(_org([code], processes_pii=True), law)

    assert listed.mandatory is True
    assert listed.jurisdiction
    assert "Consent" in listed.evidence_note
    # No other Gulf state's law leaks in.
    others = set(GULF_PRIVACY_LAWS.values()) - {law}
    assert not others & set(_names(_org([code], processes_pii=True)))


def test_gulf_privacy_laws_need_personal_data():
    assert not set(GULF_PRIVACY_LAWS.values()) & set(_names(_org(list(GULF_STATES))))


def test_gcc_is_shorthand_for_all_six_states():
    assert normalise_regions(["GCC"]) == set(GULF_STATES)
    assert set(GULF_PRIVACY_LAWS.values()) <= set(_names(_org(["GCC"], processes_pii=True)))


def test_saudi_arabia_lists_the_nca_controls_as_advisory():
    ecc = _get(_org(["SA"]), "Saudi NCA Essential Cybersecurity Controls (ECC-2:2024)")

    assert ecc.mandatory is False
    assert "2-2" in ecc.evidence_note and "2-9" in ecc.evidence_note
    assert "SDAIA AI Ethics Principles" not in _names(_org(["SA"]))
    assert _get(_org(["SA"], uses_ai_in_production=True), "SDAIA AI Ethics Principles").mandatory is False


def test_region_names_and_aliases_are_understood():
    assert normalise_regions(["uae", "KSA", "United Kingdom", "gb"]) == {"AE", "SA", "UK"}
    assert normalise_regions(None, "Saudi Arabia") == {"SA"}
    assert normalise_regions([], None) == set()
    assert normalise_regions(["APAC", 7, ""]) == {"APAC"}


# ---------------------------------------------------------------------------
# US-only laws stay in the US
# ---------------------------------------------------------------------------

def test_hipaa_is_not_listed_for_a_practice_outside_the_us():
    uae_clinic = _org(["AE"], processes_phi=True, processes_pii=True)

    assert "HIPAA" not in _names(uae_clinic)
    assert _get(uae_clinic, "UAE ICT Health Law (Federal Law No. 2 of 2019)").mandatory is True


def test_hipaa_is_still_listed_when_no_region_is_set_or_the_us_is_one_of_them():
    assert "HIPAA" in _names(_org(processes_phi=True))
    assert "HIPAA" in _names(_org(["US"], processes_phi=True))
    assert "HIPAA" in _names(_org(["US", "AE"], processes_phi=True))


# ---------------------------------------------------------------------------
# Other regions and international standards
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("code,law", [
    ("UK", "UK GDPR and Data Protection Act 2018"),
    ("IN", "India DPDP Act 2023"),
    ("CA", "PIPEDA"),
    ("AU", "Australian Privacy Act 1988"),
    ("SG", "Singapore PDPA 2012"),
])
def test_other_regions_list_their_privacy_law(code, law):
    assert _get(_org([code], processes_pii=True), law).mandatory is True
    assert law not in _names(_org([code]))


def test_iso_standards_are_advisory_and_only_outside_the_us():
    assert "ISO/IEC 27001" not in _names(_org(["US"]))
    assert "ISO/IEC 27001" not in _names(_org())
    assert _get(_org(["AE"]), "ISO/IEC 27001").mandatory is False
    assert "ISO/IEC 42001" not in _names(_org(["AE"]))
    assert _get(_org(["AE"], uses_ai_in_production=True), "ISO/IEC 42001").mandatory is False


def test_every_listed_framework_has_a_reason_and_a_link():
    org = _org(
        ["US", "EU", "UK", "GCC", "IN", "CA", "AU", "SG"],
        processes_pii=True, processes_phi=True, uses_ai_in_production=True,
        financial_services=True, processes_cardholder_data=True,
    )
    frameworks = get_applicable_frameworks(org)

    names = [f.framework for f in frameworks]
    assert len(names) == len(set(names)), "a framework is listed twice"
    for f in frameworks:
        assert f.reason.strip(), f.framework
        assert f.reference_url and f.reference_url.startswith("http"), f.framework
    # No claim of compliance or certification anywhere in the text.
    text = " ".join(f"{f.reason} {f.evidence_note or ''}" for f in frameworks).lower()
    for banned in ("compliant", "certified", "guarantee"):
        assert banned not in text


def test_the_result_is_the_same_every_time():
    org = _org(["EU", "SA"], processes_pii=True, uses_ai_in_production=True)

    first = [f.model_dump() for f in get_applicable_frameworks(org)]
    second = [f.model_dump() for f in get_applicable_frameworks(org)]

    assert first == second


def test_picking_a_region_alone_does_not_raise_the_governance_score():
    assert compute_compliance(_org()).score == 0.0
    # Advisory frameworks appear, the score does not move.
    region_only = compute_compliance(_org(["SA", "UK"]))
    assert region_only.total_frameworks > 0
    assert region_only.score == 0.0
    # A profile fact still counts, as before.
    assert compute_compliance(_org(["SA"], processes_pii=True)).score == 100.0
    assert compute_compliance(_org(uses_ai_in_production=True)).score == 100.0


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def test_endpoint_returns_the_eu_ai_act_with_its_scope_note(db_session, client_with_org):
    org = db_session.query(Organization).filter(Organization.id == OWN_ORG).first()
    org.geo_regions = json.dumps(["EU", "AE"])
    org.uses_ai_in_production = True
    org.processes_pii = True
    db_session.commit()

    resp = client_with_org.get(f"/api/governance/{OWN_ORG}/applicable-frameworks")

    assert resp.status_code == 200, resp.text
    by_name = {f["framework"]: f for f in resp.json()["frameworks"]}
    assert by_name[EU_AI_ACT]["jurisdiction"] == "European Union"
    assert "does not verify" in by_name[EU_AI_ACT]["evidence_note"]
    assert "GDPR" in by_name
    assert GULF_PRIVACY_LAWS["AE"] in by_name
