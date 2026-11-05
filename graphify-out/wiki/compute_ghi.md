# compute_ghi

> 31 nodes · cohesion 0.09

## Key Concepts

- **compute_ghi()** (25 connections) — `app/services/governance/validation_engine.py`
- **TestGHI** (17 connections) — `tests/test_igvf.py`
- **.test_all_zeros()** (3 connections) — `tests/test_igvf.py`
- **.test_audit_weight_dominant()** (3 connections) — `tests/test_igvf.py`
- **.test_compliance_weight()** (3 connections) — `tests/test_igvf.py`
- **.test_dimensions_in_result()** (3 connections) — `tests/test_igvf.py`
- **.test_grade_b_boundary()** (3 connections) — `tests/test_igvf.py`
- **.test_grade_c_boundary()** (3 connections) — `tests/test_igvf.py`
- **.test_grade_d_boundary()** (3 connections) — `tests/test_igvf.py`
- **.test_lifecycle_weight()** (3 connections) — `tests/test_igvf.py`
- **.test_perfect_scores()** (3 connections) — `tests/test_igvf.py`
- **.test_result_to_dict()** (3 connections) — `tests/test_igvf.py`
- **.test_weights_applied_correctly()** (3 connections) — `tests/test_igvf.py`
- **.test_weights_in_result()** (3 connections) — `tests/test_igvf.py`
- **.test_grade_a_boundary()** (2 connections) — `tests/test_igvf.py`
- **.test_grade_f_boundary()** (2 connections) — `tests/test_igvf.py`
- **.test_sla_weight()** (2 connections) — `tests/test_igvf.py`
- **Compute the Governance Health Index. GHI = (Audit × 0.4) + (Lifecycle × 0.3) +…** (1 connections) — `app/services/governance/validation_engine.py`
- **Test Governance Health Index computation.** (1 connections) — `tests/test_igvf.py`
- **All 100 → GHI = 100, grade A.** (1 connections) — `tests/test_igvf.py`
- **All 0 → GHI = 0, grade F.** (1 connections) — `tests/test_igvf.py`
- **Verify weight application: 80×0.4 + 60×0.3 + 40×0.2 + 100×0.1 = 68.** (1 connections) — `tests/test_igvf.py`
- **Score ≥ 80, < 90 → B.** (1 connections) — `tests/test_igvf.py`
- **Score ≥ 60, < 80 → C.** (1 connections) — `tests/test_igvf.py`
- **Score ≥ 40, < 60 → D.** (1 connections) — `tests/test_igvf.py`
- *... and 6 more nodes in this community*

## Relationships

- [_make_org](_make_org.md) (6 shared connections)
- [test_siem_integrations.py](test_siem_integrations.py.md) (3 shared connections)
- [apply_siem_multipliers](apply_siem_multipliers.md) (1 shared connections)

## Source Files

- `app/services/governance/validation_engine.py`
- `tests/test_igvf.py`

## Audit Trail

- EXTRACTED: 54 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*