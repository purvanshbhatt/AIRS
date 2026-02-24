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
            return FakeResponse("Generated narrative text")

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
    monkeypatch.setattr(ai_narrative.settings, "LLM_MODEL", "gemini-3-flash-preview", raising=False)
    monkeypatch.setattr(ai_narrative.settings, "LLM_TEMPERATURE", 0.2, raising=False)
    monkeypatch.setattr(ai_narrative.settings, "LLM_MAX_TOKENS", 256, raising=False)

    payload = {
        "overall_score": 71.0,
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
        "organization_name": "Acme Corp",
        "baseline_profiles": {},
    }

    result = ai_narrative._generate_llm_narrative(payload)

    assert result["llm_generated"] is True
    assert isinstance(result["executive_summary_text"], str)
    assert isinstance(result["roadmap_narrative_text"], str)
    assert len(calls) == 2
    exec_prompt = calls[0]["contents"]
    assert "Readiness Score" in exec_prompt
    assert "Top 3 Remediation Priorities" in exec_prompt
    assert "Do not repeat raw questionnaire answers" in exec_prompt


def test_fallback_narrative_when_llm_fails_has_required_actions():
    payload = {
        "overall_score": 52.0,
        "tier": {"label": "Needs Work", "color": "warning"},
        "domain_scores": [{"domain_id": "identity_visibility", "domain_name": "Identity", "score_5": 2.1}],
        "findings": [{"severity": "high", "title": "Weak MFA coverage"}],
        "organization_name": "Fallback Corp",
    }

    result = ai_narrative._generate_fallback_narrative(payload, llm_failed=True)
    text = result["executive_summary_text"]
    assert "Executive narrative unavailable." in text
    assert "1. Access controls" in text
    assert "2. Monitoring" in text
    assert "3. Incident response planning" in text
