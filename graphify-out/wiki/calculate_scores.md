# calculate_scores

> 54 nodes · cohesion 0.06

## Key Concepts

- **calculate_scores()** (37 connections) — `app/services/scoring.py`
- **services/scoring.py** (35 connections) — `app/services/scoring.py`
- **test_scoring.py** (15 connections) — `tests/test_scoring.py`
- **test_governance_engine.py** (14 connections) — `tests/test_governance_engine.py`
- **calculate_domain_score()** (12 connections) — `app/services/scoring.py`
- **get_recommendations()** (11 connections) — `app/services/scoring.py`
- **Any** (9 connections)
- **TestScoring** (8 connections) — `tests/test_scoring.py`
- **_calc_scores_internal()** (7 connections) — `app/services/scoring.py`
- **_score_question()** (7 connections) — `app/services/scoring.py`
- **get_assessment_recommendations()** (6 connections) — `app/api/scoring.py`
- **_get_maturity_level()** (4 connections) — `app/services/scoring.py`
- **_is_unknown_answer()** (4 connections) — `app/services/scoring.py`
- **ScoringError** (4 connections) — `app/services/scoring.py`
- **_calculate_threshold_score()** (3 connections) — `app/services/scoring.py`
- **db_session()** (3 connections) — `tests/test_governance_engine.py`
- **test_connection_error_status_enum()** (3 connections) — `tests/test_governance_engine.py`
- **test_ghi_score_update_deterministic_reliability()** (3 connections) — `tests/test_governance_engine.py`
- **test_multi_framework_mapping_creation()** (3 connections) — `tests/test_governance_engine.py`
- **TestRecommendations** (3 connections) — `tests/test_scoring.py`
- **.test_recommendations_prioritize_gaps()** (3 connections) — `tests/test_scoring.py`
- **.test_all_no_scores_zero()** (3 connections) — `tests/test_scoring.py`
- **.test_all_yes_scores_maximum()** (3 connections) — `tests/test_scoring.py`
- **.test_numeric_thresholds_retention_days()** (3 connections) — `tests/test_scoring.py`
- **.test_partial_scores()** (3 connections) — `tests/test_scoring.py`
- *... and 29 more nodes in this community*

## Relationships

- [Organization](Organization.md) (15 shared connections)
- [api/scoring.py](api-scoring.py.md) (11 shared connections)
- [api/verification.py](api-verification.py.md) (7 shared connections)
- [TelemetryVerificationService](TelemetryVerificationService.md) (7 shared connections)
- [calculate_readiness_delta](calculate_readiness_delta.md) (6 shared connections)
- [get_rubric](get_rubric.md) (5 shared connections)
- [test_findings.py](test_findings.py.md) (4 shared connections)
- [twin/engine.py](twin-engine.py.md) (3 shared connections)
- [FrameworkMappingRegistry](FrameworkMappingRegistry.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [splunk_staging_validation.py](splunk_staging_validation.py.md) (2 shared connections)
- [generate_findings](generate_findings.md) (2 shared connections)

## Source Files

- `app/api/scoring.py`
- `app/services/scoring.py`
- `tests/test_governance_engine.py`
- `tests/test_scoring.py`

## Audit Trail

- EXTRACTED: 156 (99%)
- INFERRED: 2 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*