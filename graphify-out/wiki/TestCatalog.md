# TestCatalog

> 20 nodes · cohesion 0.12

## Key Concepts

- **TestCatalog** (10 connections) — `tests/test_suggestions.py`
- **question_catalog.py** (7 connections) — `app/core/question_catalog.py`
- **get_question_metadata()** (6 connections) — `app/core/question_catalog.py`
- **get_questions_by_control_function()** (4 connections) — `app/core/question_catalog.py`
- **get_questions_by_maturity()** (4 connections) — `app/core/question_catalog.py`
- **get_all_question_metadata()** (3 connections) — `app/core/question_catalog.py`
- **Any** (2 connections)
- **.test_get_by_control_function()** (2 connections) — `tests/test_suggestions.py`
- **.test_get_by_maturity()** (2 connections) — `tests/test_suggestions.py`
- **.test_get_question_metadata_found()** (2 connections) — `tests/test_suggestions.py`
- **.test_get_question_metadata_missing()** (2 connections) — `tests/test_suggestions.py`
- **Question Suggestion Catalog Static, config-driven metadata for every rubric…** (1 connections) — `app/core/question_catalog.py`
- **Return enrichment metadata for a single question, or None.** (1 connections) — `app/core/question_catalog.py`
- **Return the full catalog.** (1 connections) — `app/core/question_catalog.py`
- **Return question IDs that map to a given NIST CSF control function.** (1 connections) — `app/core/question_catalog.py`
- **Return question IDs at a given maturity tier.** (1 connections) — `app/core/question_catalog.py`
- **Ensure question catalog covers all rubric questions.** (1 connections) — `tests/test_suggestions.py`
- **.test_each_entry_has_required_keys()** (1 connections) — `tests/test_suggestions.py`
- **.test_framework_tags_non_empty()** (1 connections) — `tests/test_suggestions.py`
- **.test_valid_enum_values()** (1 connections) — `tests/test_suggestions.py`

## Relationships

- [test_suggestions.py](test_suggestions.py.md) (5 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [get_all_question_ids](get_all_question_ids.md) (1 shared connections)

## Source Files

- `app/core/question_catalog.py`
- `tests/test_suggestions.py`

## Audit Trail

- EXTRACTED: 30 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*