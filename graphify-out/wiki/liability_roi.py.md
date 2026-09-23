# liability_roi.py

> 16 nodes · cohesion 0.18

## Key Concepts

- **liability_roi.py** (8 connections) — `app/services/liability_roi.py`
- **PortfolioROISchema** (7 connections) — `app/schemas/verification.py`
- **LiabilityROIEngine** (7 connections) — `app/services/liability_roi.py`
- **RemediationROISchema** (5 connections) — `app/schemas/verification.py`
- **.calculate_portfolio_roi()** (5 connections) — `app/services/liability_roi.py`
- **.calculate_roi()** (5 connections) — `app/services/liability_roi.py`
- **_load_benchmarks()** (4 connections) — `app/services/liability_roi.py`
- **Any** (4 connections)
- **.__init__()** (3 connections) — `app/services/liability_roi.py`
- **Per-remediation cost/time ROI metrics.** (1 connections) — `app/schemas/verification.py`
- **Aggregate ROI across all remediation actions.** (1 connections) — `app/schemas/verification.py`
- **Liability-to-ROI Engine — Quantified Risk Reduction Metrics. Maps every…** (1 connections) — `app/services/liability_roi.py`
- **Deterministic engine that calculates ROI for each remediation action.** (1 connections) — `app/services/liability_roi.py`
- **Calculate ROI for a single finding/remediation action. Args: finding: A Finding…** (1 connections) — `app/services/liability_roi.py`
- **Calculate aggregate ROI across all findings. Args: findings: List of Finding…** (1 connections) — `app/services/liability_roi.py`
- **Load the externalized ROI benchmarks configuration.** (1 connections) — `app/services/liability_roi.py`

## Relationships

- [api/verification.py](api-verification.py.md) (5 shared connections)
- [schemas/verification.py](schemas-verification.py.md) (3 shared connections)
- [BaseModel](BaseModel.md) (2 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `app/schemas/verification.py`
- `app/services/liability_roi.py`

## Audit Trail

- EXTRACTED: 32 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*