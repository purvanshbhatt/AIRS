# _detect_advisories

> 29 nodes · cohesion 0.09

## Key Concepts

- **_detect_advisories()** (20 connections) — `app/services/governance/reliability_engine.py`
- **TestAutonomousAdvisories** (14 connections) — `tests/test_reliability.py`
- **AdvisoryItem** (4 connections) — `app/services/governance/reliability_engine.py`
- **.test_advisory_has_remediation()** (4 connections) — `tests/test_reliability.py`
- **.test_advisory_to_dict()** (4 connections) — `tests/test_reliability.py`
- **.test_multiple_rules_fire_together()** (4 connections) — `tests/test_reliability.py`
- **.test_no_advisories_when_aligned()** (4 connections) — `tests/test_reliability.py`
- **.test_rule1_high_sla_no_failover()** (4 connections) — `tests/test_reliability.py`
- **.test_rule2_high_sla_low_tier()** (4 connections) — `tests/test_reliability.py`
- **.test_rule3_no_dr_plan()** (4 connections) — `tests/test_reliability.py`
- **.test_rule4_monitoring_blindspot()** (4 connections) — `tests/test_reliability.py`
- **.test_rule5_no_ir_readiness()** (4 connections) — `tests/test_reliability.py`
- **.test_rule6_no_backup_docs()** (4 connections) — `tests/test_reliability.py`
- **.test_rule7_no_rto()** (4 connections) — `tests/test_reliability.py`
- **.to_dict()** (1 connections) — `app/services/governance/reliability_engine.py`
- **Deterministic architectural misalignment advisory.** (1 connections) — `app/services/governance/reliability_engine.py`
- **Deterministic architectural misalignment detection. Triggers recommendations…** (1 connections) — `app/services/governance/reliability_engine.py`
- **Verify deterministic advisory detection rules.** (1 connections) — `tests/test_reliability.py`
- **Aligned org with good practices → no advisories.** (1 connections) — `tests/test_reliability.py`
- **Rule 1: 99.99% SLA + no failover → critical advisory.** (1 connections) — `tests/test_reliability.py`
- **Rule 2: 99.9% SLA + tier_3 → critical tier-SLA conflict.** (1 connections) — `tests/test_reliability.py`
- **Rule 3: Production SLA + no DR plan → high advisory.** (1 connections) — `tests/test_reliability.py`
- **Rule 4: High monitoring score (= poor monitoring) → high advisory.** (1 connections) — `tests/test_reliability.py`
- **Rule 5: High SLA + no IR controls → high advisory.** (1 connections) — `tests/test_reliability.py`
- **Rule 6: No backup documentation → medium advisory.** (1 connections) — `tests/test_reliability.py`
- *... and 4 more nodes in this community*

## Relationships

- [_make_org](_make_org.md) (12 shared connections)
- [Organization](Organization.md) (3 shared connections)
- [TestDimensionScorers](TestDimensionScorers.md) (2 shared connections)
- [test_reliability.py](test_reliability.py.md) (2 shared connections)
- [_auto_recommend](_auto_recommend.md) (1 shared connections)
- [fixture](fixture.md) (1 shared connections)

## Source Files

- `app/services/governance/reliability_engine.py`
- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 58 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*