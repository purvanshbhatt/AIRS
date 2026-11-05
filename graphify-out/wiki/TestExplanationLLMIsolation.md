# TestExplanationLLMIsolation

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestExplanationLLMIsolation** (4 connections) — `tests/test_explanation_service.py`
- **.test_explanation_response_includes_source_facts()** (2 connections) — `tests/test_explanation_service.py`
- **.test_llm_receives_only_source_facts()** (2 connections) — `tests/test_explanation_service.py`
- **Verify Gemini cannot modify deterministic data.** (1 connections) — `tests/test_explanation_service.py`
- **The prompt sent to Gemini contains only pre-extracted facts.** (1 connections) — `tests/test_explanation_service.py`
- **Every explanation must include the source facts for auditability.** (1 connections) — `tests/test_explanation_service.py`

## Relationships

- [test_explanation_service.py](test_explanation_service.py.md) (1 shared connections)

## Source Files

- `tests/test_explanation_service.py`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*