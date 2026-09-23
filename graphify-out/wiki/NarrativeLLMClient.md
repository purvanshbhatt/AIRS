# NarrativeLLMClient

> 7 nodes · cohesion 0.29

## Key Concepts

- **NarrativeLLMClient** (4 connections) — `app/services/narrative/llm_client.py`
- **.generate_narrative()** (3 connections) — `app/services/narrative/llm_client.py`
- **._call_genai_sdk()** (2 connections) — `app/services/narrative/llm_client.py`
- **llm_client.py** (1 connections) — `app/services/narrative/llm_client.py`
- **Wraps Google GenAI SDK calls in a strict timeout block and a generic Exception…** (1 connections) — `app/services/narrative/llm_client.py`
- **Executes the actual google.genai SDK call.** (1 connections) — `app/services/narrative/llm_client.py`
- **Client wrapper for Google GenAI SDK calls to enforce the Graceful Degradation…** (1 connections) — `app/services/narrative/llm_client.py`

## Relationships

- [get_rubric](get_rubric.md) (1 shared connections)

## Source Files

- `app/services/narrative/llm_client.py`

## Audit Trail

- EXTRACTED: 6 (86%)
- INFERRED: 1 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*