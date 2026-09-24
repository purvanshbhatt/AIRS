# api/scoring.py

> 29 nodes · cohesion 0.09

## Key Concepts

- **api/scoring.py** (22 connections) — `app/api/scoring.py`
- **validate_answers()** (9 connections) — `app/services/scoring.py`
- **AssessmentAnswers** (7 connections) — `app/schemas/scoring.py`
- **calculate_assessment_scores()** (6 connections) — `app/api/scoring.py`
- **methodology.py** (6 connections) — `app/api/v1/methodology.py`
- **get_methodology()** (6 connections) — `app/core/rubric.py`
- **validate_assessment_answers()** (5 connections) — `app/api/scoring.py`
- **get_scoring_methodology()** (4 connections) — `app/api/scoring.py`
- **get_scoring_rubric()** (4 connections) — `app/api/scoring.py`
- **list_all_questions()** (4 connections) — `app/api/scoring.py`
- **get_scoring_methodology()** (4 connections) — `app/api/v1/methodology.py`
- **TestValidation** (4 connections) — `tests/test_scoring.py`
- **get** (3 connections)
- **post** (3 connections)
- **.test_validate_missing_answers()** (2 connections) — `tests/test_scoring.py`
- **.test_validate_unknown_question_id()** (2 connections) — `tests/test_scoring.py`
- **Scoring API endpoints.** (1 connections) — `app/api/scoring.py`
- **Calculate readiness scores from assessment answers. Each domain is scored 0-5,…** (1 connections) — `app/api/scoring.py`
- **Get the complete scoring rubric definition.** (1 connections) — `app/api/scoring.py`
- **/api/v1/methodology — transparent scoring methodology. Exposes: - Rubric…** (1 connections) — `app/api/scoring.py`
- **Get a flat list of all question IDs.** (1 connections) — `app/api/scoring.py`
- **Validate assessment answers before scoring.** (1 connections) — `app/api/scoring.py`
- **get** (1 connections)
- **Methodology endpoint — GET /api/v1/methodology Returns the transparent scoring…** (1 connections) — `app/api/v1/methodology.py`
- **/api/v1/methodology Explicitly designed for: - Security auditors validating…** (1 connections) — `app/api/v1/methodology.py`
- *... and 4 more nodes in this community*

## Relationships

- [calculate_scores](calculate_scores.md) (11 shared connections)
- [get_rubric](get_rubric.md) (6 shared connections)
- [BaseSchema](BaseSchema.md) (5 shared connections)
- [app/db/database.py](app-db-database.py.md) (4 shared connections)
- [get_all_question_ids](get_all_question_ids.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/api/scoring.py`
- `app/api/v1/methodology.py`
- `app/core/rubric.py`
- `app/schemas/scoring.py`
- `app/services/scoring.py`
- `tests/test_scoring.py`

## Audit Trail

- EXTRACTED: 63 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*