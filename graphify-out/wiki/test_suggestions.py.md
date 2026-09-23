# test_suggestions.py

> 39 nodes · cohesion 0.08

## Key Concepts

- **test_suggestions.py** (16 connections) — `tests/test_suggestions.py`
- **_build_suggestions()** (15 connections) — `app/services/question_suggestions.py`
- **get_suggestions_from_answers()** (10 connections) — `app/services/question_suggestions.py`
- **_org_maturity_label()** (9 connections) — `app/services/question_suggestions.py`
- **TestBuildSuggestions** (9 connections) — `tests/test_suggestions.py`
- **_compute_function_scores_from_answers()** (6 connections) — `app/services/question_suggestions.py`
- **TestGetSuggestionsFromAnswers** (5 connections) — `tests/test_suggestions.py`
- **TestSuggestionsEndpoint** (5 connections) — `tests/test_suggestions.py`
- **_domain_to_function()** (4 connections) — `app/services/question_suggestions.py`
- **Any** (4 connections)
- **TestMaturityLabel** (4 connections) — `tests/test_suggestions.py`
- **.test_targets_weakest_function()** (3 connections) — `tests/test_suggestions.py`
- **.test_deterministic()** (3 connections) — `tests/test_suggestions.py`
- **.test_empty_answers()** (3 connections) — `tests/test_suggestions.py`
- **.test_all_perfect_returns_advanced_suggestions()** (2 connections) — `tests/test_suggestions.py`
- **.test_all_zero_returns_suggestions()** (2 connections) — `tests/test_suggestions.py`
- **.test_max_results_cap()** (2 connections) — `tests/test_suggestions.py`
- **.test_returns_list()** (2 connections) — `tests/test_suggestions.py`
- **.test_sorted_by_impact_desc()** (2 connections) — `tests/test_suggestions.py`
- **.test_suggestion_has_required_fields()** (2 connections) — `tests/test_suggestions.py`
- **.test_perfect_answers()** (2 connections) — `tests/test_suggestions.py`
- **.test_worst_answers()** (2 connections) — `tests/test_suggestions.py`
- **.test_high_score_gives_advanced()** (2 connections) — `tests/test_suggestions.py`
- **.test_low_score_gives_basic()** (2 connections) — `tests/test_suggestions.py`
- **.test_mid_score_gives_managed()** (2 connections) — `tests/test_suggestions.py`
- *... and 14 more nodes in this community*

## Relationships

- [Organization](Organization.md) (6 shared connections)
- [organizations.py](organizations.py.md) (5 shared connections)
- [TestCatalog](TestCatalog.md) (5 shared connections)
- [get_rubric](get_rubric.md) (2 shared connections)
- [calculate_scores](calculate_scores.md) (1 shared connections)
- [get_all_question_ids](get_all_question_ids.md) (1 shared connections)

## Source Files

- `app/services/question_suggestions.py`
- `tests/test_suggestions.py`

## Audit Trail

- EXTRACTED: 76 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*