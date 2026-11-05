# get_rubric

> 46 nodes · cohesion 0.06

## Key Concepts

- **get_rubric()** (41 connections) — `app/core/rubric.py`
- **rubric.py** (24 connections) — `app/core/rubric.py`
- **.get_summary()** (18 connections) — `app/services/assessment.py`
- **get_question()** (12 connections) — `app/core/rubric.py`
- **test_framework_validation.py** (10 connections) — `tests/test_framework_validation.py`
- **get_domain_nist_function()** (9 connections) — `app/core/rubric.py`
- **TestNISTCSF20Mappings** (8 connections) — `tests/test_framework_validation.py`
- **TestRubricDomainIntegrity** (5 connections) — `tests/test_framework_validation.py`
- **get_nist_functions()** (4 connections) — `app/core/rubric.py`
- **TestExplainabilityTaxonomy** (4 connections) — `tests/test_framework_validation.py`
- **_default_help_text()** (3 connections) — `app/core/rubric.py`
- **load_baseline_profiles()** (3 connections) — `app/services/assessment.py`
- **.test_deterministic_scoring_integrity_after_restore()** (3 connections) — `tests/test_dr_restore.py`
- **TestCISControlsMapping** (3 connections) — `tests/test_framework_validation.py`
- **TestFrameworkCoverageReport** (3 connections) — `tests/test_framework_validation.py`
- **.test_nist_categories_format()** (3 connections) — `tests/test_framework_validation.py`
- **.test_nist_function_lookup_returns_data()** (3 connections) — `tests/test_framework_validation.py`
- **.test_no_llm_in_rubric()** (3 connections) — `tests/test_framework_validation.py`
- **get_domain()** (2 connections) — `app/core/rubric.py`
- **.test_methodology_references_cis()** (2 connections) — `tests/test_framework_validation.py`
- **.test_coverage_report_generation()** (2 connections) — `tests/test_framework_validation.py`
- **.test_all_nist_functions_defined()** (2 connections) — `tests/test_framework_validation.py`
- **.test_every_domain_has_nist_categories()** (2 connections) — `tests/test_framework_validation.py`
- **.test_every_domain_has_nist_function()** (2 connections) — `tests/test_framework_validation.py`
- **.test_rubric_declares_nist_csf_version()** (2 connections) — `tests/test_framework_validation.py`
- *... and 21 more nodes in this community*

## Relationships

- [Organization](Organization.md) (22 shared connections)
- [api/scoring.py](api-scoring.py.md) (6 shared connections)
- [calculate_scores](calculate_scores.md) (5 shared connections)
- [ProfessionalPDFGenerator](ProfessionalPDFGenerator.md) (4 shared connections)
- [get_all_question_ids](get_all_question_ids.md) (4 shared connections)
- [twin/engine.py](twin-engine.py.md) (3 shared connections)
- [findings.py](findings.py.md) (3 shared connections)
- [main.py](main.py.md) (3 shared connections)
- [test_frameworks.py](test_frameworks.py.md) (3 shared connections)
- [Finding](Finding.md) (3 shared connections)
- [pdf.py](pdf.py.md) (2 shared connections)
- [test_suggestions.py](test_suggestions.py.md) (2 shared connections)

## Source Files

- `app/core/rubric.py`
- `app/services/assessment.py`
- `tests/test_dr_restore.py`
- `tests/test_framework_validation.py`

## Audit Trail

- EXTRACTED: 132 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*