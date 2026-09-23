# TestDowntimeBudget

> 13 nodes · cohesion 0.15

## Key Concepts

- **TestDowntimeBudget** (8 connections) — `tests/test_reliability.py`
- **.test_99_0_sla()** (3 connections) — `tests/test_reliability.py`
- **.test_99_999_sla()** (3 connections) — `tests/test_reliability.py`
- **.test_99_99_sla()** (3 connections) — `tests/test_reliability.py`
- **.test_99_9_sla()** (3 connections) — `tests/test_reliability.py`
- **.test_invalid_sla_defaults()** (3 connections) — `tests/test_reliability.py`
- **.test_to_dict()** (3 connections) — `tests/test_reliability.py`
- **Verify downtime budget calculation from SLA percentage.** (1 connections) — `tests/test_reliability.py`
- **99.9% SLA → ~525.96 minutes/year.** (1 connections) — `tests/test_reliability.py`
- **99.99% SLA → ~52.6 minutes/year.** (1 connections) — `tests/test_reliability.py`
- **99.999% SLA (five nines) → ~5.26 minutes/year.** (1 connections) — `tests/test_reliability.py`
- **99.0% SLA → ~5259 minutes/year.** (1 connections) — `tests/test_reliability.py`
- **Invalid SLA (0 or negative) defaults to 99.0%.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [simulate_breach](simulate_breach.md) (6 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)
- [_auto_recommend](_auto_recommend.md) (1 shared connections)

## Source Files

- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 20 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*