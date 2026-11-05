import sys
import types

import app.services.ai_narrative as ai_narrative


def test_generate_llm_narrative_uses_google_genai_sdk(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, text: str):
            self.text = text

    class FakeModels:
        def generate_content(self, model, contents, config):
            calls.append({"model": model, "contents": contents, "config": config})
            fake_json = """
            {
              "sections": [
                {"section_id": "executive_summary", "title": "Executive Summary", "content": "100.0"},
                {"section_id": "risk_posture", "title": "Risk Posture", "content": "..."},
                {"section_id": "governance_maturity", "title": "Governance Maturity", "content": "..."},
                {"section_id": "control_effectiveness", "title": "Control Effectiveness", "content": "..."},
                {"section_id": "compliance_status", "title": "Compliance Status", "content": "..."},
                {"section_id": "financial_exposure", "title": "Financial Exposure", "content": "..."},
                {"section_id": "threat_landscape", "title": "Threat Landscape", "content": "..."},
                {"section_id": "resource_allocation", "title": "Resource Allocation", "content": "..."},
                {"section_id": "remediation_roadmap", "title": "Remediation Roadmap", "content": "..."},
                {"section_id": "strategic_recommendations", "title": "Strategic Recommendations", "content": "..."}
              ]
            }
            """
            return FakeResponse(fake_json)

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.models = FakeModels()

    fake_google_module = types.ModuleType("google")
    fake_google_genai_module = types.ModuleType("google.genai")
    fake_google_genai_module.Client = FakeClient
    fake_google_genai_module.types = types.SimpleNamespace(
        GenerateContentConfig=lambda **kwargs: kwargs
    )
    fake_google_module.genai = fake_google_genai_module

    monkeypatch.setitem(sys.modules, "google", fake_google_module)
    monkeypatch.setitem(sys.modules, "google.genai", fake_google_genai_module)

    monkeypatch.setattr(ai_narrative.settings, "GCP_PROJECT_ID", None, raising=False)
    monkeypatch.setattr(ai_narrative.settings, "GEMINI_API_KEY", "fake-key", raising=False)
    monkeypatch.setattr(ai_narrative.settings, "LLM_MODEL", "gemini-3-flash", raising=False)
    monkeypatch.setattr(ai_narrative.settings, "LLM_TEMPERATURE", 0.2, raising=False)
    monkeypatch.setattr(ai_narrative.settings, "LLM_MAX_TOKENS", 256, raising=False)

    payload = {
        "overall_score": 100.0,
        "tier": {"label": "Good", "color": "primary"},
        "domain_scores": [
            {"domain_id": "telemetry_logging", "domain_name": "Telemetry", "score_5": 3.5}
        ],
        "findings": [
            {
                "severity": "high",
                "title": "Insufficient logging retention",
                "domain": "Telemetry",
                "recommendation": "Increase retention to 90 days",
            }
        ],
        "organization_name": "sandbox Corp",
        "baseline_profiles": {},
    }

    result = ai_narrative._generate_llm_board_story(payload)

    assert result["llm_generated"] is True
    assert "sections" in result
    assert len(result["sections"]) == 10
    assert len(calls) == 1
    exec_prompt = calls[0]["contents"]
    assert "Overall Score:" in exec_prompt


def test_fallback_narrative_when_llm_fails_has_required_actions():
    payload = {
        "overall_score": 52.0,
        "tier": {"label": "Needs Work", "color": "warning"},
        "domain_scores": [{"domain_id": "identity_visibility", "domain_name": "Identity", "score_5": 2.1}],
        "findings": [{"severity": "high", "title": "Weak MFA coverage"}],
        "organization_name": "Fallback Corp",
    }

    result = ai_narrative._generate_fallback_board_story(payload, llm_failed=True)
    sections = result["sections"]
    assert len(sections) == 10
    assert sections[0]["section_id"] == "executive_summary"
    assert "Fallback Corp scored 52.0/100" in sections[0]["content"]
