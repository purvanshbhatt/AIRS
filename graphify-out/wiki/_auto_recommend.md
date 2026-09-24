# _auto_recommend

> 25 nodes · cohesion 0.10

## Key Concepts

- **_auto_recommend()** (16 connections) — `app/services/governance/reliability_engine.py`
- **TestAutoRecommendation** (11 connections) — `tests/test_reliability.py`
- **to_dict() returns serializable dict.** (5 connections) — `tests/test_reliability.py`
- **AutoRecommendation** (4 connections) — `app/services/governance/reliability_engine.py`
- **Organization** (4 connections)
- **.test_recommendation_has_rationale()** (4 connections) — `tests/test_reliability.py`
- **.test_recommendation_source_industry()** (4 connections) — `tests/test_reliability.py`
- **.test_recommendation_to_dict()** (4 connections) — `tests/test_reliability.py`
- **.test_recommends_when_both_missing()** (4 connections) — `tests/test_reliability.py`
- **.test_recommends_when_sla_missing()** (4 connections) — `tests/test_reliability.py`
- **.test_recommends_when_tier_empty()** (4 connections) — `tests/test_reliability.py`
- **.test_recommends_when_tier_missing()** (4 connections) — `tests/test_reliability.py`
- **.test_returns_none_when_configured()** (4 connections) — `tests/test_reliability.py`
- **.test_rri_to_dict()** (4 connections) — `tests/test_reliability.py`
- **.to_dict()** (1 connections) — `app/services/governance/reliability_engine.py`
- **Auto-detected recommendation when SLA/Tier is missing.** (1 connections) — `app/services/governance/reliability_engine.py`
- **When SLA or Tier is missing, auto-detect recommended values instead of showing…** (1 connections) — `app/services/governance/reliability_engine.py`
- **Both tier + SLA missing → generates recommendation.** (1 connections) — `tests/test_reliability.py`
- **Recommendation includes non-empty rationale.** (1 connections) — `tests/test_reliability.py`
- **Known industry → source is 'industry'.** (1 connections) — `tests/test_reliability.py`
- **Verify auto-detect of missing tier/SLA.** (1 connections) — `tests/test_reliability.py`
- **Org with both tier + SLA → no recommendation.** (1 connections) — `tests/test_reliability.py`
- **Missing SLA → generates recommendation.** (1 connections) — `tests/test_reliability.py`
- **Missing tier → generates recommendation.** (1 connections) — `tests/test_reliability.py`
- **Empty tier string → generates recommendation.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [_make_org](_make_org.md) (13 shared connections)
- [Organization](Organization.md) (3 shared connections)
- [test_reliability.py](test_reliability.py.md) (2 shared connections)
- [get_sla_advisor](get_sla_advisor.md) (1 shared connections)
- [_detect_advisories](_detect_advisories.md) (1 shared connections)
- [simulate_breach](simulate_breach.md) (1 shared connections)
- [TestDowntimeBudget](TestDowntimeBudget.md) (1 shared connections)
- [TestBoardSimulation](TestBoardSimulation.md) (1 shared connections)
- [_calculate_breach_exposure](_calculate_breach_exposure.md) (1 shared connections)
- [fixture](fixture.md) (1 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 55 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*