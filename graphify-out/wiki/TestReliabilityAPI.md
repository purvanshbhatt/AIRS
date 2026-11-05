# TestReliabilityAPI

> 18 nodes · cohesion 0.11

## Key Concepts

- **TestReliabilityAPI** (11 connections) — `tests/test_reliability.py`
- **.test_200_when_staging()** (3 connections) — `tests/test_reliability.py`
- **.test_advisor_200_when_staging()** (3 connections) — `tests/test_reliability.py`
- **.test_downtime_budget_200()** (3 connections) — `tests/test_reliability.py`
- **.test_downtime_budget_400_no_sla()** (3 connections) — `tests/test_reliability.py`
- **.test_simulate_200_when_staging()** (3 connections) — `tests/test_reliability.py`
- **.test_404_org_not_found()** (2 connections) — `tests/test_reliability.py`
- **.test_404_when_not_staging()** (2 connections) — `tests/test_reliability.py`
- **.test_simulate_404_when_not_staging()** (2 connections) — `tests/test_reliability.py`
- **Test the RRI API endpoints (staging-gated).** (1 connections) — `tests/test_reliability.py`
- **Non-staging environment → 404 (invisible).** (1 connections) — `tests/test_reliability.py`
- **Staging env → 200 with full RRI result.** (1 connections) — `tests/test_reliability.py`
- **Simulation endpoint → 404 outside staging.** (1 connections) — `tests/test_reliability.py`
- **Simulation endpoint → 200 in staging.** (1 connections) — `tests/test_reliability.py`
- **SLA Advisor → 200 in staging.** (1 connections) — `tests/test_reliability.py`
- **Downtime budget → 200 in staging.** (1 connections) — `tests/test_reliability.py`
- **Downtime budget without SLA → 400.** (1 connections) — `tests/test_reliability.py`
- **Nonexistent org → 404.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [_make_org](_make_org.md) (5 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)
- [fixture](fixture.md) (1 shared connections)

## Source Files

- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*