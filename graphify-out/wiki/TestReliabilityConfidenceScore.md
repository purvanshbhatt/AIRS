# TestReliabilityConfidenceScore

> 24 nodes · cohesion 0.08

## Key Concepts

- **TestReliabilityConfidenceScore** (13 connections) — `tests/test_reliability.py`
- **.test_all_positive_answers()** (3 connections) — `tests/test_reliability.py`
- **.test_architecture_redundancy_with_tech()** (3 connections) — `tests/test_reliability.py`
- **.test_backup_validation_combined()** (3 connections) — `tests/test_reliability.py`
- **.test_dr_test_recency_scoring()** (3 connections) — `tests/test_reliability.py`
- **.test_max_score_100()** (3 connections) — `tests/test_reliability.py`
- **.test_moderate_band()** (3 connections) — `tests/test_reliability.py`
- **.test_no_answers()** (3 connections) — `tests/test_reliability.py`
- **.test_rcs_to_dict()** (3 connections) — `tests/test_reliability.py`
- **.test_sub_scores_dict()** (3 connections) — `tests/test_reliability.py`
- **.test_verified_band()** (3 connections) — `tests/test_reliability.py`
- **.test_rcs_weights_sum_to_one()** (2 connections) — `tests/test_reliability.py`
- **Verify RCS 5-dimensional scoring and bands.** (1 connections) — `tests/test_reliability.py`
- **Full positive answers → high RCS.** (1 connections) — `tests/test_reliability.py`
- **No answers → Unvalidated band.** (1 connections) — `tests/test_reliability.py`
- **High scoring → Verified band (≥75).** (1 connections) — `tests/test_reliability.py`
- **Mid-range scores → Moderate band (50-74).** (1 connections) — `tests/test_reliability.py`
- **DR test True → 18 points, False → 3 points.** (1 connections) — `tests/test_reliability.py`
- **Backup doc + restore → max 20.** (1 connections) — `tests/test_reliability.py`
- **Tech items in HA categories boost architecture score.** (1 connections) — `tests/test_reliability.py`
- **sub_scores dict contains all 5 dimensions.** (1 connections) — `tests/test_reliability.py`
- **RCS dimension weights must sum to 1.0.** (1 connections) — `tests/test_reliability.py`
- **to_dict() returns full serializable dict.** (1 connections) — `tests/test_reliability.py`
- **Total score cannot exceed 100.** (1 connections) — `tests/test_reliability.py`

## Relationships

- [calculate_rcs](calculate_rcs.md) (10 shared connections)
- [test_reliability.py](test_reliability.py.md) (1 shared connections)

## Source Files

- `tests/test_reliability.py`

## Audit Trail

- EXTRACTED: 34 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*