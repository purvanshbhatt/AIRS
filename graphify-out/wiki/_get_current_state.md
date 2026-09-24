# _get_current_state

> 21 nodes · cohesion 0.14

## Key Concepts

- **_get_current_state()** (9 connections) — `app/api/v1/decisions.py`
- **project_decisions()** (9 connections) — `app/api/v1/decisions.py`
- **test_decisions_api.py** (9 connections) — `tests/test_decisions_api.py`
- **get_recommended_actions()** (8 connections) — `app/api/v1/decisions.py`
- **DecisionAction** (7 connections) — `app/schemas/decision.py`
- **decision.py** (6 connections) — `app/schemas/decision.py`
- **ProjectReadinessRequest** (6 connections) — `app/schemas/decision.py`
- **ProjectReadinessResponse** (4 connections) — `app/schemas/decision.py`
- **RecommendedAction** (4 connections) — `app/schemas/decision.py`
- **Session** (3 connections)
- **setup_org()** (3 connections) — `tests/test_decisions_api.py`
- **test_project_readiness_api()** (3 connections) — `tests/test_decisions_api.py`
- **test_project_readiness_api_too_many_actions()** (2 connections) — `tests/test_decisions_api.py`
- **Any** (1 connections)
- **get** (1 connections)
- **post** (1 connections)
- **Projects the readiness score given a set of hypothetical actions.** (1 connections) — `app/api/v1/decisions.py`
- **Returns a prioritized list of recommended actions that would increase readiness…** (1 connections) — `app/api/v1/decisions.py`
- **ProjectReadinessRequest** (1 connections)
- **fixture** (1 connections)
- **test_recommended_actions_api()** (1 connections) — `tests/test_decisions_api.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (8 shared connections)
- [Organization](Organization.md) (5 shared connections)
- [BaseModel](BaseModel.md) (4 shared connections)
- [calculate_readiness_delta](calculate_readiness_delta.md) (3 shared connections)
- [v1/readiness.py](v1-readiness.py.md) (1 shared connections)

## Source Files

- `app/api/v1/decisions.py`
- `app/schemas/decision.py`
- `tests/test_decisions_api.py`

## Audit Trail

- EXTRACTED: 44 (86%)
- INFERRED: 7 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*