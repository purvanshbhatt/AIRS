# _make_org

> 52 nodes · cohesion 0.06

## Key Concepts

- **_make_org()** (61 connections) — `tests/test_reliability.py`
- **calculate_rri()** (48 connections) — `app/services/governance/reliability_engine.py`
- **TestCompositeRRI** (14 connections) — `tests/test_reliability.py`
- **TestRRIv2Integration** (11 connections) — `tests/test_reliability.py`
- **_log_rri_audit_event()** (8 connections) — `app/services/governance/reliability_engine.py`
- **Session** (4 connections)
- **ReliabilityRiskResult** (4 connections) — `app/services/governance/reliability_engine.py`
- **.test_basic_rri_calculation()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_all_dimensions_weighted()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_dimension_keys()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_downtime_budget_included()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_downtime_budget_none_without_sla()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_tier_3_reduced()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_tier_multiplier_applied()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_top_gaps_capped()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_with_custom_answers()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_with_high_sla()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_with_low_sla()** (4 connections) — `tests/test_reliability.py`
- **.test_audit_event_created_on_calculate()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_has_advisories()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_has_auto_recommendation_when_missing()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_has_breach_exposure()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_has_rcs()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_no_auto_recommendation_when_configured()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_to_dict_includes_v2_fields()** (4 connections) — `tests/test_reliability.py`
- *... and 27 more nodes in this community*

## Relationships

- [_auto_recommend](_auto_recommend.md) (13 shared connections)
- [_detect_advisories](_detect_advisories.md) (12 shared connections)
- [TestDimensionScorers](TestDimensionScorers.md) (7 shared connections)
- [test_reliability.py](test_reliability.py.md) (6 shared connections)
- [Organization](Organization.md) (6 shared connections)
- [fixture](fixture.md) (6 shared connections)
- [TestRRIv2API](TestRRIv2API.md) (6 shared connections)
- [TestBoardSimulation](TestBoardSimulation.md) (5 shared connections)
- [TestReliabilityAPI](TestReliabilityAPI.md) (5 shared connections)
- [calculate_rcs](calculate_rcs.md) (3 shared connections)
- [simulate_breach](simulate_breach.md) (3 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 161 (98%)
- INFERRED: 4 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*