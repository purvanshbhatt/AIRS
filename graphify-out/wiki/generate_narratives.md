# generate_narratives

> 27 nodes · cohesion 0.12

## Key Concepts

- **generate_narratives()** (18 connections) — `app/api/narratives.py`
- **get_executive_summary()** (9 connections) — `app/api/narratives.py`
- **get_roadmap()** (9 connections) — `app/api/narratives.py`
- **narrative.py** (9 connections) — `app/schemas/narrative.py`
- **NarrativeType** (8 connections) — `app/schemas/narrative.py`
- **NarrativeRequest** (7 connections) — `app/schemas/narrative.py`
- **get_llm_status()** (5 connections) — `app/api/narratives.py`
- **FindingRewrite** (5 connections) — `app/schemas/narrative.py`
- **NarrativeContent** (5 connections) — `app/schemas/narrative.py`
- **NarrativeResponse** (5 connections) — `app/schemas/narrative.py`
- **LLMStatusResponse** (4 connections) — `app/schemas/narrative.py`
- **get** (3 connections)
- **Session** (3 connections)
- **User** (3 connections)
- **Enum** (2 connections)
- **post** (1 connections)
- **Get just the executive summary narrative. Convenience endpoint for quick access.** (1 connections) — `app/api/narratives.py`
- **Get just the 30/60/90 day roadmap narrative. Convenience endpoint for quick…** (1 connections) — `app/api/narratives.py`
- **Get LLM feature status. Returns whether LLM narratives are enabled and…** (1 connections) — `app/api/narratives.py`
- **Generate AI-assisted narratives for an assessment. IMPORTANT: The LLM cannot…** (1 connections) — `app/api/narratives.py`
- **str** (1 connections)
- **Pydantic schemas for LLM Narrative generation.** (1 connections) — `app/schemas/narrative.py`
- **Types of narratives available.** (1 connections) — `app/schemas/narrative.py`
- **Request for narrative generation.** (1 connections) — `app/schemas/narrative.py`
- **Single narrative content.** (1 connections) — `app/schemas/narrative.py`
- *... and 2 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (11 shared connections)
- [BaseModel](BaseModel.md) (5 shared connections)
- [User](User.md) (3 shared connections)
- [test_llm_narrative.py](test_llm_narrative.py.md) (2 shared connections)
- [generate_findings](generate_findings.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [ScoreContext](ScoreContext.md) (1 shared connections)
- [FindingContext](FindingContext.md) (1 shared connections)

## Source Files

- `app/api/narratives.py`
- `app/schemas/narrative.py`

## Audit Trail

- EXTRACTED: 53 (80%)
- INFERRED: 13 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*