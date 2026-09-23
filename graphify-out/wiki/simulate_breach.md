# simulate_breach

> 20 nodes · cohesion 0.12

## Key Concepts

- **simulate_breach()** (16 connections) — `app/services/governance/reliability_engine.py`
- **calculate_downtime_budget()** (15 connections) — `app/services/governance/reliability_engine.py`
- **_format_minutes()** (8 connections) — `app/services/governance/reliability_engine.py`
- **TestFormatMinutes** (5 connections) — `tests/test_reliability.py`
- **BreachSimulation** (4 connections) — `app/services/governance/reliability_engine.py`
- **DowntimeBudget** (4 connections) — `app/services/governance/reliability_engine.py`
- **.test_hours()** (3 connections) — `tests/test_reliability.py`
- **.test_minutes()** (3 connections) — `tests/test_reliability.py`
- **.test_seconds()** (3 connections) — `tests/test_reliability.py`
- **.test_days()** (2 connections) — `tests/test_reliability.py`
- **.to_dict()** (1 connections) — `app/services/governance/reliability_engine.py`
- **.to_dict()** (1 connections) — `app/services/governance/reliability_engine.py`
- **Board Simulation Mode: What if we upgraded SLA from X to Y? Shows required…** (1 connections) — `app/services/governance/reliability_engine.py`
- **Calculated downtime budget from SLA target.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Board Simulation Mode result.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Calculate annual and monthly downtime budgets from SLA percentage.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Format minutes into human-readable duration.** (1 connections) — `app/services/governance/reliability_engine.py`
- **< 1 minute → seconds.** (1 connections) — `tests/test_reliability.py`
- **1-59 minutes → minutes.** (1 connections) — `tests/test_reliability.py`
- **60-1440 minutes → hours.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [Organization](Organization.md) (6 shared connections)
- [TestDowntimeBudget](TestDowntimeBudget.md) (6 shared connections)
- [TestBoardSimulation](TestBoardSimulation.md) (5 shared connections)
- [test_reliability.py](test_reliability.py.md) (4 shared connections)
- [_make_org](_make_org.md) (3 shared connections)
- [_get_org](_get_org.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [_auto_recommend](_auto_recommend.md) (1 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 50 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*