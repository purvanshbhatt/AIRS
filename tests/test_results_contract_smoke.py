def _submit_min_answers(client, assessment_id: str):
    answers = [
        {"question_id": "tl_01", "value": "false"},
        {"question_id": "dc_01", "value": "20"},
        {"question_id": "iv_01", "value": "false"},
        {"question_id": "ir_01", "value": "false"},
        {"question_id": "rs_01", "value": "false"},
    ]
    response = client.post(f"/api/assessments/{assessment_id}/answers", json={"answers": answers})
    assert response.status_code == 200


def test_assessment_summary_contract_includes_framework_and_analytics_fields(client):
    org_resp = client.post("/api/orgs", json={"name": "Smoke Org"})
    org_id = org_resp.json()["id"]

    assessment_resp = client.post("/api/assessments", json={"organization_id": org_id, "title": "Smoke Assessment"})
    assessment_id = assessment_resp.json()["id"]

    _submit_min_answers(client, assessment_id)

    score_resp = client.post(f"/api/assessments/{assessment_id}/score")
    assert score_resp.status_code == 200

    summary_resp = client.get(f"/api/assessments/{assessment_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()

    assert "product" in summary
    assert summary["product"]["name"]
    assert "framework_mapping" in summary
    assert "analytics" in summary
    assert "detailed_roadmap" in summary

    framework_mapping = summary["framework_mapping"]
    assert "findings" in framework_mapping

    analytics = summary["analytics"]
    assert "risk_summary" in analytics
    assert "detection_gaps" in analytics

    risk_summary = analytics["risk_summary"]
    assert "severity_counts" in risk_summary
    assert "findings_count" in risk_summary
    assert "total_risk_score" in risk_summary

    detection_categories = analytics["detection_gaps"].get("categories", [])
    if detection_categories:
        category = detection_categories[0]
        assert "category" in category
        assert "gap_count" in category
        assert "is_critical" in category
