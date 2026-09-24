# TestDeterministicFallback

> 11 nodes · cohesion 0.20

## Key Concepts

- **TestDeterministicFallback** (11 connections) — `tests/test_llm_narrative.py`
- **fixture** (3 connections)
- **.sample_findings()** (3 connections) — `tests/test_llm_narrative.py`
- **.sample_scores()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_fallback_executive_summary()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_fallback_finding_rewrite()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_fallback_roadmap()** (3 connections) — `tests/test_llm_narrative.py`
- **Fallback should produce valid executive summary.** (1 connections) — `tests/test_llm_narrative.py`
- **Fallback should produce valid roadmap.** (1 connections) — `tests/test_llm_narrative.py`
- **Fallback should produce valid finding rewrite.** (1 connections) — `tests/test_llm_narrative.py`
- **Tests for deterministic fallback when LLM is disabled.** (1 connections) — `tests/test_llm_narrative.py`

## Relationships

- [LLMNarrativeGenerator](LLMNarrativeGenerator.md) (4 shared connections)
- [ScoreContext](ScoreContext.md) (3 shared connections)
- [test_llm_narrative.py](test_llm_narrative.py.md) (2 shared connections)
- [FindingContext](FindingContext.md) (2 shared connections)

## Source Files

- `tests/test_llm_narrative.py`

## Audit Trail

- EXTRACTED: 18 (82%)
- INFERRED: 4 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*