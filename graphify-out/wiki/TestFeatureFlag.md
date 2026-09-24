# TestFeatureFlag

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestFeatureFlag** (6 connections) — `tests/test_llm_narrative.py`
- **.test_generator_needs_api_key()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_generator_not_available_when_disabled()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_llm_disabled_by_default()** (2 connections) — `tests/test_llm_narrative.py`
- **Tests for AIRS_USE_LLM feature flag.** (1 connections) — `tests/test_llm_narrative.py`
- **LLM should be disabled by default.** (1 connections) — `tests/test_llm_narrative.py`
- **Generator should not be available when disabled.** (1 connections) — `tests/test_llm_narrative.py`
- **Generator should require API key even when enabled.** (1 connections) — `tests/test_llm_narrative.py`

## Relationships

- [LLMNarrativeGenerator](LLMNarrativeGenerator.md) (3 shared connections)
- [test_llm_narrative.py](test_llm_narrative.py.md) (1 shared connections)

## Source Files

- `tests/test_llm_narrative.py`

## Audit Trail

- EXTRACTED: 10 (91%)
- INFERRED: 1 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*