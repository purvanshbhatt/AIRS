# FindingContext

> 16 nodes · cohesion 0.16

## Key Concepts

- **FindingContext** (20 connections) — `app/services/llm_narrative.py`
- **TestRoadmapGeneration** (7 connections) — `tests/test_llm_narrative.py`
- **TestFindingRewrites** (6 connections) — `tests/test_llm_narrative.py`
- **.test_critical_findings_in_first_phase()** (5 connections) — `tests/test_llm_narrative.py`
- **.test_roadmap_phases_present()** (5 connections) — `tests/test_llm_narrative.py`
- **.test_recommendation_included()** (4 connections) — `tests/test_llm_narrative.py`
- **.test_severity_preserved()** (4 connections) — `tests/test_llm_narrative.py`
- **.to_prompt_context()** (2 connections) — `app/services/llm_narrative.py`
- **Immutable finding context passed to LLM (read-only).** (1 connections) — `app/services/llm_narrative.py`
- **Format finding for LLM prompt.** (1 connections) — `app/services/llm_narrative.py`
- **Tests for 30/60/90 day roadmap generation.** (1 connections) — `tests/test_llm_narrative.py`
- **Roadmap should contain all three phases.** (1 connections) — `tests/test_llm_narrative.py`
- **Critical findings should appear in 30-day phase.** (1 connections) — `tests/test_llm_narrative.py`
- **Tests for business-tone finding rewrites.** (1 connections) — `tests/test_llm_narrative.py`
- **Original severity should be preserved in rewrite.** (1 connections) — `tests/test_llm_narrative.py`
- **Recommendation should be included in rewrite.** (1 connections) — `tests/test_llm_narrative.py`

## Relationships

- [LLMNarrativeGenerator](LLMNarrativeGenerator.md) (12 shared connections)
- [test_llm_narrative.py](test_llm_narrative.py.md) (4 shared connections)
- [ScoreContext](ScoreContext.md) (3 shared connections)
- [TestDeterministicFallback](TestDeterministicFallback.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [generate_narratives](generate_narratives.md) (1 shared connections)

## Source Files

- `app/services/llm_narrative.py`
- `tests/test_llm_narrative.py`

## Audit Trail

- EXTRACTED: 35 (83%)
- INFERRED: 7 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*