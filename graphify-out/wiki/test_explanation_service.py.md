# test_explanation_service.py

> 22 nodes · cohesion 0.17

## Key Concepts

- **test_explanation_service.py** (13 connections) — `tests/test_explanation_service.py`
- **TestExplanationSchemas** (10 connections) — `tests/test_explanation_service.py`
- **schemas/explanation.py** (9 connections) — `app/schemas/explanation.py`
- **ExplanationRequest** (8 connections) — `app/schemas/explanation.py`
- **ExplanationResponse** (7 connections) — `app/schemas/explanation.py`
- **Audience** (6 connections) — `app/schemas/explanation.py`
- **ExplanationContent** (6 connections) — `app/schemas/explanation.py`
- **SourceFact** (6 connections) — `app/schemas/explanation.py`
- **SubjectType** (6 connections) — `app/schemas/explanation.py`
- **.test_explanation_response_schema()** (4 connections) — `tests/test_explanation_service.py`
- **Enum** (3 connections)
- **str** (2 connections)
- **.test_explanation_request_schema()** (2 connections) — `tests/test_explanation_service.py`
- **Pydantic schemas for the Explanation (Business Language) API. Gemini transforms…** (1 connections) — `app/schemas/explanation.py`
- **Types of subjects that can be explained.** (1 connections) — `app/schemas/explanation.py`
- **Target audience for the explanation.** (1 connections) — `app/schemas/explanation.py`
- **Request body for generating a business-language explanation.** (1 connections) — `app/schemas/explanation.py`
- **A deterministic fact that grounds the explanation.** (1 connections) — `app/schemas/explanation.py`
- **The generated explanation payload.** (1 connections) — `app/schemas/explanation.py`
- **Response from the explanation endpoint.** (1 connections) — `app/schemas/explanation.py`
- **Explanation API Test Suite — LLM Isolation & Source-Fact Grounding. Validates:…** (1 connections) — `tests/test_explanation_service.py`
- **Test the Pydantic schemas for explanation API.** (1 connections) — `tests/test_explanation_service.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [BaseModel](BaseModel.md) (4 shared connections)
- [create_explanation](create_explanation.md) (1 shared connections)
- [ExplanationService](ExplanationService.md) (1 shared connections)
- [TestExplanationServiceInit](TestExplanationServiceInit.md) (1 shared connections)
- [TestExplanationDeterministicFallback](TestExplanationDeterministicFallback.md) (1 shared connections)
- [TestExplanationLLMIsolation](TestExplanationLLMIsolation.md) (1 shared connections)

## Source Files

- `app/schemas/explanation.py`
- `tests/test_explanation_service.py`

## Audit Trail

- EXTRACTED: 45 (87%)
- INFERRED: 7 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*