# get_sla_advisor

> 15 nodes · cohesion 0.18

## Key Concepts

- **get_sla_advisor()** (14 connections) — `app/services/governance/reliability_engine.py`
- **TestSLAAdvisor** (8 connections) — `tests/test_reliability.py`
- **SLAAdvisorRecommendation** (4 connections) — `app/services/governance/reliability_engine.py`
- **_cached_sla_advisor()** (3 connections) — `app/services/governance/reliability_engine.py`
- **.test_education()** (2 connections) — `tests/test_reliability.py`
- **.test_fintech()** (2 connections) — `tests/test_reliability.py`
- **.test_healthcare()** (2 connections) — `tests/test_reliability.py`
- **.test_none_industry()** (2 connections) — `tests/test_reliability.py`
- **.test_to_dict()** (2 connections) — `tests/test_reliability.py`
- **.test_unknown_industry()** (2 connections) — `tests/test_reliability.py`
- **Smart SLA Advisor output.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Cached industry SLA lookup (industry rarely changes).** (1 connections) — `app/services/governance/reliability_engine.py`
- **Smart SLA Advisor: recommend tier and SLA range based on industry (cached).** (1 connections) — `app/services/governance/reliability_engine.py`
- **.to_dict()** (1 connections) — `app/services/governance/reliability_engine.py`
- **Verify industry-aware SLA recommendations.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [Organization](Organization.md) (3 shared connections)
- [test_reliability.py](test_reliability.py.md) (2 shared connections)
- [_auto_recommend](_auto_recommend.md) (1 shared connections)
- [_make_org](_make_org.md) (1 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*