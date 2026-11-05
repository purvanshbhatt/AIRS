# _calculate_breach_exposure

> 24 nodes · cohesion 0.11

## Key Concepts

- **_calculate_breach_exposure()** (13 connections) — `app/services/governance/reliability_engine.py`
- **TestBreachExposureBadge** (11 connections) — `tests/test_reliability.py`
- **BreachExposureBadge** (4 connections) — `app/services/governance/reliability_engine.py`
- **.test_boundary_25()** (3 connections) — `tests/test_reliability.py`
- **.test_boundary_just_above_25()** (3 connections) — `tests/test_reliability.py`
- **.test_breach_exposure_to_dict()** (3 connections) — `tests/test_reliability.py`
- **.test_breach_high_elevated_scores()** (3 connections) — `tests/test_reliability.py`
- **.test_contractual_risk_extreme_scores()** (3 connections) — `tests/test_reliability.py`
- **.test_no_sla_target()** (3 connections) — `tests/test_reliability.py`
- **.test_sla_strain_moderate_scores()** (3 connections) — `tests/test_reliability.py`
- **.test_within_budget_low_scores()** (3 connections) — `tests/test_reliability.py`
- **.test_badge_emoji_present()** (2 connections) — `tests/test_reliability.py`
- **.to_dict()** (1 connections) — `app/services/governance/reliability_engine.py`
- **4-level executive breach exposure classification.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Calculate 4-level executive breach exposure badge. Derived from declared SLA vs…** (1 connections) — `app/services/governance/reliability_engine.py`
- **Verify 4-level executive breach exposure badge calculation.** (1 connections) — `tests/test_reliability.py`
- **Low recovery + SLA scores → within_budget (green).** (1 connections) — `tests/test_reliability.py`
- **Moderate scores → sla_strain (yellow).** (1 connections) — `tests/test_reliability.py`
- **High scores → breach_high (red).** (1 connections) — `tests/test_reliability.py`
- **Very high scores → contractual_risk (black).** (1 connections) — `tests/test_reliability.py`
- **When SLA is None → sla_strain with explanation about missing config.** (1 connections) — `tests/test_reliability.py`
- **All levels have non-empty badge string.** (1 connections) — `tests/test_reliability.py`
- **Exposure exactly 25 → within_budget.** (1 connections) — `tests/test_reliability.py`
- **Exposure 26 → sla_strain.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [Organization](Organization.md) (2 shared connections)
- [test_reliability.py](test_reliability.py.md) (2 shared connections)
- [_make_org](_make_org.md) (1 shared connections)
- [_auto_recommend](_auto_recommend.md) (1 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 36 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*