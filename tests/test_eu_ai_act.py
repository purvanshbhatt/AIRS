"""
EU AI Act inventory: classification rules and the API around them.

The class comes from fixed rules over the owner's answers. These tests pin the
rules (so a wording change cannot move a system between classes unnoticed),
the owner checks, and the input limits.
"""
import json

import pytest

from app.db.durable_mirror import MIRROR_SPECS
from app.models.ai_act_system import AIActSystem
from app.models.organization import Organization
from app.services.governance import eu_ai_act
from app.services.governance.eu_ai_act import classify

OWN_ORG = "test-org-123"  # provisioned by the client_with_org fixture
OTHER_ORG = "someone-elses-org"
BASE = f"/api/v1/ai-act/{OWN_ORG}/systems"


def _ids(result):
    return [d["id"] for d in result["obligations"]]


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def test_no_ticks_is_minimal_risk_with_ai_literacy_only():
    result = classify("deployer", {})

    assert result["risk_class"] == "minimal"
    assert _ids(result) == ["ai_literacy"]
    assert result["exception_note"] is None


@pytest.mark.parametrize("key", [key for key, _, _ in eu_ai_act.PROHIBITED_PRACTICES])
def test_every_banned_practice_gives_prohibited(key):
    # A banned practice wins over everything else that is ticked.
    result = classify("deployer", {key: True, "employment": True, "talks_to_people": True, "limited_role": True})

    assert result["risk_class"] == "prohibited"
    assert _ids(result) == ["stop_prohibited"]
    assert result["basis"][0]["article"].startswith("Article 5(1)")


@pytest.mark.parametrize("key", [key for key, _, _ in eu_ai_act.HIGH_RISK_AREAS])
def test_every_annex_iii_area_gives_high_risk(key):
    result = classify("deployer", {key: True})

    assert result["risk_class"] == "high"
    assert result["basis"][0]["article"].startswith("Annex III")
    assert {"human_oversight", "keep_logs", "tell_people", "ai_literacy"} <= set(_ids(result))


def test_a_regulated_product_is_high_risk_and_the_limited_role_exception_cannot_undo_it():
    result = classify("provider", {"regulated_product": True, "limited_role": True})

    assert result["risk_class"] == "high"
    assert result["basis"][0]["article"] == "Article 6(1) and Annex I"


def test_limited_role_takes_an_annex_iii_use_out_of_high_risk_and_says_what_to_record():
    result = classify("deployer", {"employment": True, "limited_role": True})

    assert result["risk_class"] == "minimal"
    assert "Article 6(3)" in result["exception_note"]
    assert "Article 6(4)" in result["exception_note"]
    assert "human_oversight" not in _ids(result)


def test_profiling_people_cancels_the_limited_role_exception():
    result = classify("deployer", {"employment": True, "limited_role": True, "profiles_people": True})

    assert result["risk_class"] == "high"
    assert result["exception_note"] is None
    assert any("profiles people" in b["text"] for b in result["basis"])


def test_provider_and_deployer_get_different_high_risk_duties():
    deployer = set(_ids(classify("deployer", {"education": True})))
    provider = set(_ids(classify("provider", {"education": True})))

    assert "keep_logs" in deployer and "keep_logs" not in provider
    assert {"risk_management", "conformity_assessment", "registration"} <= provider
    assert not {"risk_management", "conformity_assessment"} & deployer


def test_fundamental_rights_assessment_only_where_article_27_can_apply():
    assert "fundamental_rights_assessment" not in _ids(classify("deployer", {"employment": True}))
    assert "fundamental_rights_assessment" in _ids(classify("deployer", {"employment": True, "public_service": True}))
    assert "fundamental_rights_assessment" in _ids(classify("deployer", {"essential_services": True}))
    assert "fundamental_rights_assessment" not in _ids(classify("provider", {"essential_services": True}))


def test_a_chatbot_is_limited_risk_and_the_duty_sits_with_whoever_built_it():
    deployer = classify("deployer", {"talks_to_people": True, "generates_content": True})
    provider = classify("provider", {"talks_to_people": True, "generates_content": True})

    assert deployer["risk_class"] == provider["risk_class"] == "limited"
    assert {d["id"]: d["duty_of"] for d in deployer["obligations"]} == {
        "ai_literacy": "you", "tell_users_ai": "supplier", "mark_generated_content": "supplier",
    }
    assert {d["duty_of"] for d in provider["obligations"]} == {"you"}


def test_deployer_transparency_duties():
    result = classify("deployer", {"emotion_or_biometric_categorisation": True, "deepfake": True})

    assert result["risk_class"] == "limited"
    assert {"tell_people_exposed", "disclose_deepfake"} <= set(_ids(result))


def test_high_risk_keeps_its_transparency_duties():
    result = classify("deployer", {"essential_services": True, "talks_to_people": True})

    assert result["risk_class"] == "high"
    assert "tell_users_ai" in _ids(result)


def test_false_and_missing_answers_mean_the_same():
    assert classify("deployer", {"employment": False}) == classify("deployer", {})


def test_same_answers_same_result_and_unique_duty_ids():
    answers = {"essential_services": True, "public_service": True, "talks_to_people": True, "deepfake": True}

    first, second = classify("deployer", answers), classify("deployer", dict(answers))

    assert first == second
    assert len(_ids(first)) == len(set(_ids(first)))


def test_unknown_input_is_refused_not_guessed():
    with pytest.raises(ValueError):
        classify("auditor", {})
    with pytest.raises(ValueError):
        classify("deployer", {"made_up_key": True})


def test_wording_never_claims_compliance():
    text = json.dumps([eu_ai_act.questionnaire(), classify("provider", {"employment": True})]).lower()

    for banned in ("compliant", "certified", "guarantee", "approved"):
        assert banned not in text
    assert "not legal advice" in eu_ai_act.DISCLAIMER


def test_every_question_in_the_questionnaire_is_a_known_answer_key():
    keys = [o["key"] for s in eu_ai_act.questionnaire()["sections"] for o in s["options"]]

    assert len(keys) == len(set(keys))
    assert set(keys) == set(eu_ai_act.ANSWER_KEYS)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def _payload(**overrides):
    body = {
        "name": "  Scribe   Assistant ",
        "purpose": "Drafts visit notes from a recording for the clinician to review.",
        "vendor": "Example Vendor",
        "role": "deployer",
        "answers": {"generates_content": True},
    }
    body.update(overrides)
    return body


def test_create_list_update_delete(db_session, client_with_org):
    created = client_with_org.post(BASE, json=_payload())
    assert created.status_code == 201, created.text
    system = created.json()
    assert system["name"] == "Scribe Assistant"
    assert system["risk_class"] == "limited"
    assert all(d["status"] == "not_answered" for d in system["obligations"])

    listed = client_with_org.get(BASE).json()
    assert listed["total"] == 1
    assert listed["by_risk_class"] == {"prohibited": 0, "high": 0, "limited": 1, "minimal": 0}
    assert "not legal advice" in listed["disclaimer"]

    updated = client_with_org.put(f"{BASE}/{system['id']}", json=_payload(answers={"essential_services": True}))
    assert updated.status_code == 200, updated.text
    assert updated.json()["risk_class"] == "high"

    deleted = client_with_org.delete(f"{BASE}/{system['id']}")
    assert deleted.status_code == 200, deleted.text
    assert client_with_org.get(BASE).json()["total"] == 0
    assert db_session.query(AIActSystem).count() == 0


def test_only_ticked_answers_are_stored(db_session, client_with_org):
    client_with_org.post(BASE, json=_payload(answers={"employment": True, "education": False}))

    stored = json.loads(db_session.query(AIActSystem).one().answers)

    assert stored == {"employment": True}


def test_owner_statement_per_duty_is_kept_and_dropped_when_the_duty_no_longer_applies(client_with_org):
    system = client_with_org.post(BASE, json=_payload(answers={"employment": True})).json()
    url = f"{BASE}/{system['id']}"

    resp = client_with_org.put(f"{url}/obligations/keep_logs", json={"status": "in_place"})
    assert resp.status_code == 200, resp.text
    status = {d["id"]: d["status"] for d in resp.json()["obligations"]}
    assert status["keep_logs"] == "in_place"
    assert status["human_oversight"] == "not_answered"

    # A duty that does not apply to this system cannot be answered.
    assert client_with_org.put(f"{url}/obligations/registration", json={"status": "in_place"}).status_code == 404
    assert client_with_org.put(f"{url}/obligations/keep_logs", json={"status": "verified"}).status_code == 422

    # The system stops being high-risk: the old statement must not linger.
    client_with_org.put(url, json=_payload(answers={}))
    back = client_with_org.put(url, json=_payload(answers={"employment": True})).json()
    assert {d["id"]: d["status"] for d in back["obligations"]}["keep_logs"] == "not_answered"


@pytest.mark.parametrize("bad", [
    {"name": "   "},
    {"name": "x" * 121},
    {"purpose": ""},
    {"purpose": "x" * 1001},
    {"role": "auditor"},
    {"answers": {"made_up_key": True}},
    {"answers": {"employment": "yes please"}},
])
def test_bad_input_is_rejected_and_nothing_is_stored(db_session, client_with_org, bad):
    resp = client_with_org.post(BASE, json=_payload(**bad))

    assert resp.status_code == 422, resp.text
    assert db_session.query(AIActSystem).count() == 0


def test_another_organisations_inventory_cannot_be_read_or_changed(db_session, client_with_org):
    db_session.add(Organization(id=OTHER_ORG, name="Other Practice", owner_uid="another-user"))
    db_session.add(AIActSystem(id="sys-other", org_id=OTHER_ORG, name="Theirs", purpose="x", role="deployer"))
    db_session.commit()
    other = f"/api/v1/ai-act/{OTHER_ORG}/systems"

    assert client_with_org.get(other).status_code == 404
    assert client_with_org.post(other, json=_payload()).status_code == 404
    assert client_with_org.delete(f"{other}/sys-other").status_code == 404
    # Their system is not reachable through the caller's own organisation either.
    assert client_with_org.delete(f"{BASE}/sys-other").status_code == 404
    assert client_with_org.put(f"{BASE}/sys-other", json=_payload()).status_code == 404
    assert client_with_org.put(f"{BASE}/sys-other/obligations/ai_literacy", json={"status": "in_place"}).status_code == 404
    assert db_session.query(AIActSystem).filter(AIActSystem.org_id == OTHER_ORG).count() == 1


def test_a_corrupt_stored_row_does_not_break_the_list(db_session, client_with_org):
    db_session.add(AIActSystem(
        id="sys-bad", org_id=OWN_ORG, name="Old row", purpose="x", role="deployer",
        answers="not json", obligation_status='{"ai_literacy": "verified"}',
    ))
    db_session.commit()

    item = client_with_org.get(BASE).json()["systems"][0]

    assert item["risk_class"] == "minimal"
    # A status the rules do not know is never shown as if it were real.
    assert item["obligations"][0]["status"] == "not_answered"


def test_questionnaire_endpoint(client_with_org):
    resp = client_with_org.get("/api/v1/ai-act/questionnaire")

    assert resp.status_code == 200, resp.text
    assert [s["id"] for s in resp.json()["sections"]] == ["prohibited", "high_risk", "exception", "transparency"]


def test_inventory_is_copied_to_durable_storage_and_erased_with_the_organisation():
    assert "ai_act_systems" in {spec.table for spec in MIRROR_SPECS}
    # Data erasure finds organisation tables by their org_id column.
    assert "org_id" in AIActSystem.__table__.c
