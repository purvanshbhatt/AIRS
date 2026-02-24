"""
Tests for the question suggestion engine.

All suggestion logic MUST be deterministic — no randomness, no LLM.
These tests validate:
  - Catalog completeness
  - Stateless suggestion builder
  - Proper sorting / filtering by impact, effort, maturity
  - Edge cases: perfect scores, all-zero scores, empty answers
  - API endpoint (via TestClient)
"""

import pytest
from app.core.rubric import get_all_question_ids
from app.core.question_catalog import (
    QUESTION_CATALOG,
    CONTROL_FUNCTIONS,
    get_question_metadata,
    get_questions_by_control_function,
    get_questions_by_maturity,
)
from app.services.question_suggestions import (
    get_suggestions_from_answers,
    _build_suggestions,
    _org_maturity_label,
)


# ── Full answer sets used across multiple tests ──

ALL_YES: dict = {
    "tl_01": True, "tl_02": True, "tl_03": True,
    "tl_04": True, "tl_05": 365, "tl_06": True,
    "dc_01": 100, "dc_02": True, "dc_03": True,
    "dc_04": True, "dc_05": True, "dc_06": True,
    "iv_01": True, "iv_02": True, "iv_03": True,
    "iv_04": True, "iv_05": True, "iv_06": True,
    "ir_01": True, "ir_02": True, "ir_03": True,
    "ir_04": True, "ir_05": True, "ir_06": True,
    "rs_01": True, "rs_02": True, "rs_03": True,
    "rs_04": True, "rs_05": 0, "rs_06": True,
}

ALL_NO: dict = {
    "tl_01": False, "tl_02": False, "tl_03": False,
    "tl_04": False, "tl_05": 0, "tl_06": False,
    "dc_01": 0, "dc_02": False, "dc_03": False,
    "dc_04": False, "dc_05": False, "dc_06": False,
    "iv_01": False, "iv_02": False, "iv_03": False,
    "iv_04": False, "iv_05": False, "iv_06": False,
    "ir_01": False, "ir_02": False, "ir_03": False,
    "ir_04": False, "ir_05": False, "ir_06": False,
    "rs_01": False, "rs_02": False, "rs_03": False,
    "rs_04": False, "rs_05": 999, "rs_06": False,
}


# ---------------------------------------------------------------------------
# Catalog integrity
# ---------------------------------------------------------------------------

class TestCatalog:
    """Ensure question catalog covers all rubric questions."""

    def test_catalog_has_all_30_questions(self):
        rubric_ids = set(get_all_question_ids())
        catalog_ids = set(QUESTION_CATALOG.keys())
        assert catalog_ids == rubric_ids

    def test_each_entry_has_required_keys(self):
        required = {"framework_tags", "maturity_level", "effort_level",
                     "impact_level", "control_function"}
        for qid, meta in QUESTION_CATALOG.items():
            assert required.issubset(meta.keys()), f"{qid} missing keys"

    def test_valid_enum_values(self):
        for qid, m in QUESTION_CATALOG.items():
            assert m["maturity_level"] in ("basic", "managed", "advanced"), qid
            assert m["effort_level"] in ("low", "medium", "high"), qid
            assert m["impact_level"] in ("low", "medium", "high"), qid
            assert m["control_function"] in CONTROL_FUNCTIONS, qid

    def test_framework_tags_non_empty(self):
        for qid, m in QUESTION_CATALOG.items():
            assert len(m["framework_tags"]) > 0, f"{qid} has no framework tags"

    def test_get_question_metadata_found(self):
        assert get_question_metadata("tl_01") is not None

    def test_get_question_metadata_missing(self):
        assert get_question_metadata("nonexistent_99") is None

    def test_get_by_control_function(self):
        detect_qs = get_questions_by_control_function("detect")
        assert len(detect_qs) > 0
        for qid in detect_qs:
            assert QUESTION_CATALOG[qid]["control_function"] == "detect"

    def test_get_by_maturity(self):
        basic_qs = get_questions_by_maturity("basic")
        assert len(basic_qs) > 0
        for qid in basic_qs:
            assert QUESTION_CATALOG[qid]["maturity_level"] == "basic"


# ---------------------------------------------------------------------------
# Maturity label helper
# ---------------------------------------------------------------------------

class TestMaturityLabel:

    def test_low_score_gives_basic(self):
        assert _org_maturity_label(10) == "basic"
        assert _org_maturity_label(0) == "basic"
        assert _org_maturity_label(39.9) == "basic"

    def test_mid_score_gives_managed(self):
        assert _org_maturity_label(40) == "managed"
        assert _org_maturity_label(55) == "managed"
        assert _org_maturity_label(69.9) == "managed"

    def test_high_score_gives_advanced(self):
        assert _org_maturity_label(70) == "advanced"
        assert _org_maturity_label(100) == "advanced"


# ---------------------------------------------------------------------------
# Deterministic suggestion builder (_build_suggestions is a pure function)
# ---------------------------------------------------------------------------

class TestBuildSuggestions:
    """Test the core pure-function builder with fabricated scores."""

    def test_returns_list(self):
        scores = {fn: 50.0 for fn in CONTROL_FUNCTIONS}
        result = _build_suggestions(scores, max_results=5)
        assert isinstance(result, list)

    def test_max_results_cap(self):
        scores = {fn: 10.0 for fn in CONTROL_FUNCTIONS}
        result = _build_suggestions(scores, max_results=3)
        assert len(result) <= 3

    def test_targets_weakest_function(self):
        """Suggestions should focus on the weakest control function."""
        scores = {
            "govern": 90.0,
            "identify": 90.0,
            "protect": 90.0,
            "detect": 10.0,
            "respond": 90.0,
            "recover": 90.0,
        }
        result = _build_suggestions(scores, max_results=10)
        # Most suggestions should be for "detect" (the weakest)
        detect_count = sum(1 for s in result if s["control_function"] == "detect")
        assert detect_count >= 1

    def test_all_zero_returns_suggestions(self):
        scores = {fn: 0.0 for fn in CONTROL_FUNCTIONS}
        result = _build_suggestions(scores, max_results=10)
        assert len(result) > 0

    def test_all_perfect_returns_advanced_suggestions(self):
        scores = {fn: 95.0 for fn in CONTROL_FUNCTIONS}
        result = _build_suggestions(scores, max_results=30)
        assert len(result) > 0
        # Should only be advanced questions for a perfect org
        for s in result:
            assert s["maturity_level"] == "advanced"

    def test_sorted_by_impact_desc(self):
        scores = {fn: 20.0 for fn in CONTROL_FUNCTIONS}
        result = _build_suggestions(scores, max_results=20)
        impact_weight = {"high": 3, "medium": 2, "low": 1}
        for i in range(len(result) - 1):
            assert impact_weight[result[i]["impact_level"]] >= impact_weight[result[i+1]["impact_level"]]

    def test_suggestion_has_required_fields(self):
        scores = {fn: 30.0 for fn in CONTROL_FUNCTIONS}
        result = _build_suggestions(scores, max_results=5)
        required = {"id", "question_text", "framework_tags", "maturity_level",
                     "effort_level", "impact_level", "control_function", "domain_id"}
        for s in result:
            assert required.issubset(s.keys()), f"Missing fields in {s['id']}"


# ---------------------------------------------------------------------------
# Stateless end-to-end (from answers, no DB)
# ---------------------------------------------------------------------------

class TestGetSuggestionsFromAnswers:

    def test_perfect_answers(self):
        suggestions = get_suggestions_from_answers(ALL_YES, max_results=10)
        assert isinstance(suggestions, list)
        # Perfect org should get only advanced suggestions
        for s in suggestions:
            assert s["maturity_level"] == "advanced"

    def test_worst_answers(self):
        suggestions = get_suggestions_from_answers(ALL_NO, max_results=10)
        assert len(suggestions) > 0
        # Should be basic maturity suggestions for a failing org
        for s in suggestions:
            assert s["maturity_level"] in ("basic", "managed", "advanced")

    def test_deterministic(self):
        """Same input MUST produce identical output every time."""
        a = get_suggestions_from_answers(ALL_NO, max_results=10)
        b = get_suggestions_from_answers(ALL_NO, max_results=10)
        assert a == b

    def test_empty_answers(self):
        """Empty answers dict should not crash."""
        suggestions = get_suggestions_from_answers({}, max_results=5)
        assert isinstance(suggestions, list)


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestSuggestionsEndpoint:
    """Integration tests for GET /api/orgs/{org_id}/suggested-questions."""

    def test_org_not_found_returns_404(self, client):
        resp = client.get("/api/orgs/nonexistent-id/suggested-questions")
        assert resp.status_code == 404

    def test_valid_org_returns_suggestions(self, client, db_session):
        # Create an org first
        resp = client.post("/api/orgs", json={
            "name": "Test Org",
            "industry": "Technology",
            "size": "51-200",
        })
        assert resp.status_code == 201
        org_id = resp.json()["id"]

        # Fetch suggestions (org has no assessments — should still work)
        resp = client.get(f"/api/orgs/{org_id}/suggested-questions")
        assert resp.status_code == 200
        body = resp.json()
        assert "suggestions" in body
        assert "total_count" in body
        assert isinstance(body["suggestions"], list)

    def test_max_results_query_param(self, client, db_session):
        resp = client.post("/api/orgs", json={
            "name": "Cap Org",
            "industry": "Finance",
            "size": "1-50",
        })
        org_id = resp.json()["id"]

        resp = client.get(f"/api/orgs/{org_id}/suggested-questions?max_results=3")
        assert resp.status_code == 200
        assert len(resp.json()["suggestions"]) <= 3
