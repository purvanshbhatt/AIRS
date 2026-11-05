# verify_restore

> 7 nodes · cohesion 0.48

## Key Concepts

- **verify_restore()** (5 connections) — `scripts/verify_dr_restore.py`
- **verify_dr_restore.py** (4 connections) — `scripts/verify_dr_restore.py`
- **create_mock_s3_snapshot()** (4 connections) — `scripts/verify_dr_restore.py`
- **main()** (4 connections) — `scripts/verify_dr_restore.py`
- **Path** (3 connections)
- **Verify restored database integrity across all 9 DR validation criteria.** (1 connections) — `scripts/verify_dr_restore.py`
- **Create a realistic mock database backup representing an S3 export bundle.** (1 connections) — `scripts/verify_dr_restore.py`

## Relationships

- [get_rubric](get_rubric.md) (2 shared connections)

## Source Files

- `scripts/verify_dr_restore.py`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*