# get_all_question_ids

> 9 nodes · cohesion 0.22

## Key Concepts

- **get_all_question_ids()** (7 connections) — `app/core/rubric.py`
- **TestRubric** (6 connections) — `tests/test_scoring.py`
- **.test_each_domain_has_six_questions()** (2 connections) — `tests/test_scoring.py`
- **.test_rubric_has_five_domains()** (2 connections) — `tests/test_scoring.py`
- **.test_total_questions_is_30()** (2 connections) — `tests/test_scoring.py`
- **.test_weights_total_100()** (2 connections) — `tests/test_scoring.py`
- **.test_catalog_has_all_30_questions()** (2 connections) — `tests/test_suggestions.py`
- **Return a flat list of all question IDs.** (1 connections) — `app/core/rubric.py`
- **Tests for rubric structure.** (1 connections) — `tests/test_scoring.py`

## Relationships

- [get_rubric](get_rubric.md) (4 shared connections)
- [calculate_scores](calculate_scores.md) (2 shared connections)
- [api/scoring.py](api-scoring.py.md) (1 shared connections)
- [test_suggestions.py](test_suggestions.py.md) (1 shared connections)
- [TestCatalog](TestCatalog.md) (1 shared connections)

## Source Files

- `app/core/rubric.py`
- `tests/test_scoring.py`
- `tests/test_suggestions.py`

## Audit Trail

- EXTRACTED: 17 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*