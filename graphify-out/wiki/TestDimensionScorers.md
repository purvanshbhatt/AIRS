# TestDimensionScorers

> 46 nodes · cohesion 0.06

## Key Concepts

- **TestDimensionScorers** (16 connections) — `tests/test_reliability.py`
- **RRIDimension** (10 connections) — `app/services/governance/reliability_engine.py`
- **_score_sla_commitment()** (10 connections) — `app/services/governance/reliability_engine.py`
- **_score_recovery_capability()** (9 connections) — `app/services/governance/reliability_engine.py`
- **Any** (8 connections)
- **_score_bcdr_validation()** (8 connections) — `app/services/governance/reliability_engine.py`
- **_score_monitoring_detection()** (8 connections) — `app/services/governance/reliability_engine.py`
- **_score_redundancy_ha()** (8 connections) — `app/services/governance/reliability_engine.py`
- **_get_architecture_alignment()** (4 connections) — `app/services/governance/reliability_engine.py`
- **.test_bcdr_good_ir()** (3 connections) — `tests/test_reliability.py`
- **.test_bcdr_no_data()** (3 connections) — `tests/test_reliability.py`
- **.test_monitoring_good_coverage()** (3 connections) — `tests/test_reliability.py`
- **.test_monitoring_no_data()** (3 connections) — `tests/test_reliability.py`
- **.test_recovery_good_controls()** (3 connections) — `tests/test_reliability.py`
- **.test_recovery_no_answers()** (3 connections) — `tests/test_reliability.py`
- **.test_recovery_rto_undefined()** (3 connections) — `tests/test_reliability.py`
- **.test_redundancy_no_data()** (3 connections) — `tests/test_reliability.py`
- **.test_redundancy_with_ha_tech()** (3 connections) — `tests/test_reliability.py`
- **.test_sla_high_target()** (3 connections) — `tests/test_reliability.py`
- **.test_sla_low_target()** (3 connections) — `tests/test_reliability.py`
- **.test_sla_mismatch_tier()** (3 connections) — `tests/test_reliability.py`
- **.test_sla_no_target()** (3 connections) — `tests/test_reliability.py`
- **.test_sla_weight()** (3 connections) — `tests/test_reliability.py`
- **Single RRI dimension score.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Determine architecture alignment from dimension scores.** (1 connections) — `app/services/governance/reliability_engine.py`
- *... and 21 more nodes in this community*

## Relationships

- [_make_org](_make_org.md) (7 shared connections)
- [Organization](Organization.md) (7 shared connections)
- [test_reliability.py](test_reliability.py.md) (6 shared connections)
- [calculate_rcs](calculate_rcs.md) (2 shared connections)
- [_detect_advisories](_detect_advisories.md) (2 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 85 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*