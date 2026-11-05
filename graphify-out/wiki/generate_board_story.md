# generate_board_story

> 8 nodes · cohesion 0.39

## Key Concepts

- **generate_board_story()** (12 connections) — `app/services/ai_narrative.py`
- **_generate_fallback_board_story()** (11 connections) — `app/services/ai_narrative.py`
- **_generate_llm_board_story()** (7 connections) — `app/services/ai_narrative.py`
- **Any** (4 connections)
- **test_ai_narrative_genai.py** (3 connections) — `tests/test_ai_narrative_genai.py`
- **test_fallback_narrative_when_llm_fails_has_required_actions()** (2 connections) — `tests/test_ai_narrative_genai.py`
- **test_generate_llm_narrative_uses_google_genai_sdk()** (2 connections) — `tests/test_ai_narrative_genai.py`
- **Generate 10 structured narrative sections for the Board Story.** (1 connections) — `app/services/ai_narrative.py`

## Relationships

- [ai_narrative.py](ai_narrative.py.md) (6 shared connections)
- [TestFallbackNarrative](TestFallbackNarrative.md) (5 shared connections)
- [test_ai_narrative.py](test_ai_narrative.py.md) (3 shared connections)
- [_build_summary_payload](_build_summary_payload.md) (2 shared connections)
- [TestGenerateNarrative](TestGenerateNarrative.md) (2 shared connections)
- [TestLLMNarrativeGeneration](TestLLMNarrativeGeneration.md) (1 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `app/services/ai_narrative.py`
- `tests/test_ai_narrative_genai.py`

## Audit Trail

- EXTRACTED: 30 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*