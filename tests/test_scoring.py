"""
Tests for the scoring service.
"""

import pytest
from app.services.scoring import (
    calculate_scores,
    calculate_domain_score,
    get_recommendations,
    validate_answers
)
from app.core.rubric import get_rubric, get_all_question_ids


class TestRubric:
    """Tests for rubric structure."""
    
    def test_rubric_has_five_domains(self):
        rubric = get_rubric()
        assert len(rubric["domains"]) == 5
    
    def test_weights_total_100(self):
        rubric = get_rubric()
        total_weight = sum(d["weight"] for d in rubric["domains"].values())
        assert total_weight == 100
    
    def test_each_domain_has_six_questions(self):
        rubric = get_rubric()
        for domain_id, domain in rubric["domains"].items():
            assert len(domain["questions"]) == 6, f"{domain_id} should have 6 questions"
    
    def test_total_questions_is_30(self):
        question_ids = get_all_question_ids()
        assert len(question_ids) == 30


class TestScoring:
    """Tests for scoring calculations."""
    
    def test_all_yes_scores_maximum(self):
        """All boolean 'yes' answers should give max scores."""
        answers = {
            "tl_01": True, "tl_02": True, "tl_03": True, 
            "tl_04": True, "tl_05": 365, "tl_06": True,
            "dc_01": 100, "dc_02": True, "dc_03": True,
            "dc_04": True, "dc_05": True, "dc_06": True,
            "iv_01": True, "iv_02": True, "iv_03": True,
            "iv_04": True, "iv_05": True, "iv_06": True,
            "ir_01": True, "ir_02": True, "ir_03": True,
            "ir_04": True, "ir_05": True, "ir_06": True,
            "rs_01": True, "rs_02": True, "rs_03": True,
            "rs_04": True, "rs_05": 0, "rs_06": True,  # RTO: 0 = immediate, best
        }
        
        result = calculate_scores(answers)
        
        assert result["overall_score"] == 100
        assert result["maturity_level"] == 5
        for domain in result["domains"]:
            assert domain["score"] == 5.0
    
    def test_all_no_scores_zero(self):
        """All 'no' answers should give zero scores."""
        answers = {
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
        
        result = calculate_scores(answers)
        
        assert result["overall_score"] == 0
        assert result["maturity_level"] == 1
    
    def test_partial_scores(self):
        """Partial answers should produce proportional scores."""
        # 3 out of 6 yes in telemetry domain
        answers = {
            "tl_01": True, "tl_02": True, "tl_03": True,
            "tl_04": False, "tl_05": 0, "tl_06": False,
        }
        
        result = calculate_domain_score("telemetry_logging", answers)
        
        assert result["score"] == 2.5  # 3/6 * 5 = 2.5
    
    def test_numeric_thresholds_retention_days(self):
        """Test log retention thresholds."""
        # 90 days should give 0.75 points
        answers = {"tl_05": 90}
        result = calculate_domain_score("telemetry_logging", answers)
        
        q_score = next(q for q in result["questions"] if q["question_id"] == "tl_05")
        assert q_score["points_earned"] == 0.75
    
    def test_percentage_thresholds_edr(self):
        """Test EDR coverage percentage thresholds."""
        answers = {"dc_01": 85}  # 85% should give 0.75 points
        result = calculate_domain_score("detection_coverage", answers)
        
        q_score = next(q for q in result["questions"] if q["question_id"] == "dc_01")
        assert q_score["points_earned"] == 0.75
    
    def test_rto_lower_is_better(self):
        """Test RTO scoring where lower values are better."""
        # 4 hours RTO should give full points
        answers = {"rs_05": 4}
        result = calculate_domain_score("resilience", answers)
        
        q_score = next(q for q in result["questions"] if q["question_id"] == "rs_05")
        assert q_score["points_earned"] == 1.0
        
        # 72 hours RTO should give 0.5 points
        answers = {"rs_05": 72}
        result = calculate_domain_score("resilience", answers)
        
        q_score = next(q for q in result["questions"] if q["question_id"] == "rs_05")
        assert q_score["points_earned"] == 0.5


class TestMaturityLevels:
    """Tests for maturity level determination."""
    
    def test_maturity_level_1(self):
        result = calculate_scores({})  # Empty answers
        assert result["maturity_level"] == 1
        assert result["maturity_name"] == "Initial"
    
    def test_maturity_level_boundaries(self):
        """Test that score boundaries map to correct levels."""
        rubric = get_rubric()
        
        expected = {
            0: 1, 20: 1,
            21: 2, 40: 2,
            41: 3, 60: 3,
            61: 4, 80: 4,
            81: 5, 100: 5
        }
        
        for score, expected_level in expected.items():
            for range_key, level_info in rubric["maturity_levels"].items():
                low, high = map(int, range_key.split("-"))
                if low <= score <= high:
                    assert level_info["level"] == expected_level


class TestRecommendations:
    """Tests for recommendation generation."""
    
    def test_recommendations_prioritize_gaps(self):
        answers = {
            "tl_01": False, "tl_02": True, "tl_03": True,
            "tl_04": True, "tl_05": 365, "tl_06": True,
        }
        
        scores = calculate_scores(answers)
        recommendations = get_recommendations(scores)
        
        # Should have at least one recommendation for the 'no' answer
        assert len(recommendations) > 0
        
        # First rec should be from lowest scoring domain
        lowest_domain = min(scores["domains"], key=lambda x: x["score"])
        assert recommendations[0]["domain_id"] == lowest_domain["domain_id"]


class TestValidation:
    """Tests for answer validation."""
    
    def test_validate_unknown_question_id(self):
        answers = {"unknown_id": True}
        result = validate_answers(answers)
        
        assert not result["valid"]
        assert "Unknown question ID: unknown_id" in result["errors"]
    
    def test_validate_missing_answers(self):
        answers = {"tl_01": True}  # Only one answer
        result = validate_answers(answers)
        
        assert result["valid"]  # Missing answers are warnings, not errors
        assert len(result["warnings"]) == 29  # 30 - 1 = 29 missing


class TestAPIEndpoints:
    """Tests for API endpoints."""
    
    def test_get_rubric(self, client):
        response = client.get("/api/scoring/rubric")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert len(data["domains"]) == 5
    
    def test_get_questions(self, client):
        response = client.get("/api/scoring/questions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 30
    
    def test_calculate_scores(self, client):
        answers = {
            "tl_01": True, "tl_02": True, "tl_03": False,
            "tl_04": True, "tl_05": 90, "tl_06": True,
            "dc_01": 85, "dc_02": True, "dc_03": True,
            "dc_04": False, "dc_05": True, "dc_06": True,
            "iv_01": False, "iv_02": True, "iv_03": True,
            "iv_04": False, "iv_05": False, "iv_06": True,
            "ir_01": True, "ir_02": False, "ir_03": True,
            "ir_04": True, "ir_05": True, "ir_06": False,
            "rs_01": True, "rs_02": True, "rs_03": False,
            "rs_04": True, "rs_05": 24, "rs_06": True,
        }
        
        response = client.post("/api/scoring/calculate", json={"answers": answers})
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100
        assert "maturity_level" in data
        assert len(data["domains"]) == 5
    
    def test_validate_answers(self, client):
        response = client.post("/api/scoring/validate", json={"answers": {"tl_01": True}})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
    
    def test_get_recommendations(self, client):
        answers = {"tl_01": False, "tl_02": False}
        response = client.post("/api/scoring/recommendations", json={"answers": answers})
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
