# ScoreContext

> 17 nodes · cohesion 0.15

## Key Concepts

- **ScoreContext** (22 connections) — `app/services/llm_narrative.py`
- **TestExecutiveSummaryGeneration** (7 connections) — `tests/test_llm_narrative.py`
- **TestScoreImmutability** (5 connections) — `tests/test_llm_narrative.py`
- **.generator()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_high_score_positive_tone()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_low_score_urgent_tone()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_prompt_context_contains_exact_scores()** (3 connections) — `tests/test_llm_narrative.py`
- **.test_score_context_is_readonly()** (3 connections) — `tests/test_llm_narrative.py`
- **.to_prompt_context()** (2 connections) — `app/services/llm_narrative.py`
- **Immutable score context passed to LLM (read-only).** (1 connections) — `app/services/llm_narrative.py`
- **Format scores for LLM prompt (read-only display).** (1 connections) — `app/services/llm_narrative.py`
- **Tests for executive summary generation.** (1 connections) — `tests/test_llm_narrative.py`
- **High scores should result in positive summary.** (1 connections) — `tests/test_llm_narrative.py`
- **Low scores should result in urgent summary.** (1 connections) — `tests/test_llm_narrative.py`
- **Tests ensuring LLM cannot modify scores.** (1 connections) — `tests/test_llm_narrative.py`
- **ScoreContext should preserve original values.** (1 connections) — `tests/test_llm_narrative.py`
- **Prompt context should contain exact score values.** (1 connections) — `tests/test_llm_narrative.py`

## Relationships

- [LLMNarrativeGenerator](LLMNarrativeGenerator.md) (7 shared connections)
- [test_llm_narrative.py](test_llm_narrative.py.md) (4 shared connections)
- [TestDeterministicFallback](TestDeterministicFallback.md) (3 shared connections)
- [FindingContext](FindingContext.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [generate_narratives](generate_narratives.md) (1 shared connections)

## Source Files

- `app/services/llm_narrative.py`
- `tests/test_llm_narrative.py`

## Audit Trail

- EXTRACTED: 33 (85%)
- INFERRED: 6 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*