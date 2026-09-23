# TestRiskBands

> 14 nodes · cohesion 0.21

## Key Concepts

- **TestRiskBands** (10 connections) — `tests/test_reliability.py`
- **_get_breach_probability()** (8 connections) — `app/services/governance/reliability_engine.py`
- **_get_risk_band()** (8 connections) — `app/services/governance/reliability_engine.py`
- **.test_breach_high()** (2 connections) — `tests/test_reliability.py`
- **.test_breach_low()** (2 connections) — `tests/test_reliability.py`
- **.test_breach_moderate()** (2 connections) — `tests/test_reliability.py`
- **.test_breach_negligible()** (2 connections) — `tests/test_reliability.py`
- **.test_critical()** (2 connections) — `tests/test_reliability.py`
- **.test_high()** (2 connections) — `tests/test_reliability.py`
- **.test_low()** (2 connections) — `tests/test_reliability.py`
- **.test_moderate()** (2 connections) — `tests/test_reliability.py`
- **Map RRI score to risk band.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Map RRI score to estimated breach probability.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Verify score → risk band & breach probability mapping.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [test_reliability.py](test_reliability.py.md) (3 shared connections)
- [_make_org](_make_org.md) (2 shared connections)
- [Organization](Organization.md) (2 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 26 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*