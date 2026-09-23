# LLMNarrativeGenerator

> 25 nodes · cohesion 0.14

## Key Concepts

- **LLMNarrativeGenerator** (30 connections) — `app/services/llm_narrative.py`
- **.generate_executive_summary()** (9 connections) — `app/services/llm_narrative.py`
- **.generate_roadmap_narrative()** (8 connections) — `app/services/llm_narrative.py`
- **NarrativeResult** (8 connections) — `app/services/llm_narrative.py`
- **._fallback_executive_summary()** (7 connections) — `app/services/llm_narrative.py`
- **.rewrite_finding_business_tone()** (7 connections) — `app/services/llm_narrative.py`
- **._fallback_roadmap()** (6 connections) — `app/services/llm_narrative.py`
- **._generate_content()** (6 connections) — `app/services/llm_narrative.py`
- **.is_available()** (6 connections) — `app/services/llm_narrative.py`
- **._fallback_finding_rewrite()** (5 connections) — `app/services/llm_narrative.py`
- **._get_weak_domains()** (5 connections) — `app/services/llm_narrative.py`
- **._get_client()** (4 connections) — `app/services/llm_narrative.py`
- **.__init__()** (1 connections) — `app/services/llm_narrative.py`
- **Generates AI-assisted narratives from deterministic assessment data. IMPORTANT:…** (1 connections) — `app/services/llm_narrative.py`
- **Lazy-load Google Gemini client.** (1 connections) — `app/services/llm_narrative.py`
- **Check if LLM features are available.** (1 connections) — `app/services/llm_narrative.py`
- **Generate content using Gemini.** (1 connections) — `app/services/llm_narrative.py`
- **Generate an executive summary paragraph. The LLM receives READ-ONLY score data…** (1 connections) — `app/services/llm_narrative.py`
- **Generate a 30/60/90 day roadmap narrative. Prioritizes findings by severity and…** (1 connections) — `app/services/llm_narrative.py`
- **Rewrite a technical finding in business-friendly language. Preserves severity…** (1 connections) — `app/services/llm_narrative.py`
- **Get domains with lowest scores.** (1 connections) — `app/services/llm_narrative.py`
- **Deterministic fallback when LLM is unavailable.** (1 connections) — `app/services/llm_narrative.py`
- **Deterministic fallback roadmap.** (1 connections) — `app/services/llm_narrative.py`
- **Deterministic fallback for finding rewrite.** (1 connections) — `app/services/llm_narrative.py`
- **Result from narrative generation.** (1 connections) — `app/services/llm_narrative.py`

## Relationships

- [FindingContext](FindingContext.md) (12 shared connections)
- [ScoreContext](ScoreContext.md) (7 shared connections)
- [test_llm_narrative.py](test_llm_narrative.py.md) (4 shared connections)
- [TestDeterministicFallback](TestDeterministicFallback.md) (4 shared connections)
- [TestFeatureFlag](TestFeatureFlag.md) (3 shared connections)

## Source Files

- `app/services/llm_narrative.py`

## Audit Trail

- EXTRACTED: 67 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*