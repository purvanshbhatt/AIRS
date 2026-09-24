# TestBoardSimulation

> 11 nodes · cohesion 0.18

## Key Concepts

- **TestBoardSimulation** (7 connections) — `tests/test_reliability.py`
- **.test_simulate_downgrade()** (4 connections) — `tests/test_reliability.py`
- **.test_simulate_five_nines()** (4 connections) — `tests/test_reliability.py`
- **.test_simulate_preserves_org()** (4 connections) — `tests/test_reliability.py`
- **.test_simulate_to_dict()** (4 connections) — `tests/test_reliability.py`
- **.test_simulate_upgrade()** (4 connections) — `tests/test_reliability.py`
- **Test breach simulation (What-if analysis).** (1 connections) — `tests/test_reliability.py`
- **Simulating SLA upgrade returns valid result.** (1 connections) — `tests/test_reliability.py`
- **Simulating SLA downgrade → less stringent.** (1 connections) — `tests/test_reliability.py`
- **Simulation does not persist changes to org.** (1 connections) — `tests/test_reliability.py`
- **Upgrade to 99.99% → significant improvements required.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [_make_org](_make_org.md) (5 shared connections)
- [simulate_breach](simulate_breach.md) (5 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)
- [_auto_recommend](_auto_recommend.md) (1 shared connections)

## Source Files

- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*