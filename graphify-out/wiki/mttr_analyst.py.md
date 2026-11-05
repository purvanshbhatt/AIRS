# mttr_analyst.py

> 33 nodes · cohesion 0.10

## Key Concepts

- **mttr_analyst.py** (15 connections) — `app/services/mttr_analyst.py`
- **MTTRAnalystAgent** (10 connections) — `app/services/mttr_analyst.py`
- **.generate_executive_summary()** (10 connections) — `app/services/mttr_analyst.py`
- **._generate_llm_summary()** (8 connections) — `app/services/mttr_analyst.py`
- **Any** (7 connections)
- **_fetch_historical_ghi()** (6 connections) — `app/services/mttr_analyst.py`
- **._generate_deterministic_summary()** (6 connections) — `app/services/mttr_analyst.py`
- **_calculate_mttr_from_logs()** (5 connections) — `app/services/mttr_analyst.py`
- **_fetch_remediation_logs()** (5 connections) — `app/services/mttr_analyst.py`
- **get_mttr_analyst_agent()** (5 connections) — `app/services/mttr_analyst.py`
- **._build_chart_data()** (5 connections) — `app/services/mttr_analyst.py`
- **_calculate_liability_exposure()** (4 connections) — `app/services/mttr_analyst.py`
- **._get_client()** (4 connections) — `app/services/mttr_analyst.py`
- **_compute_trend()** (3 connections) — `app/services/mttr_analyst.py`
- **get_historical_ghi_scores()** (3 connections) — `app/services/mttr_analyst.py`
- **get_remediation_audit_logs()** (3 connections) — `app/services/mttr_analyst.py`
- **.is_available()** (3 connections) — `app/services/mttr_analyst.py`
- **.__init__()** (1 connections) — `app/services/mttr_analyst.py`
- **MTTR Analyst Agent — Board-Ready Risk-Reduction Analysis. Provides: 1. A…** (1 connections) — `app/services/mttr_analyst.py`
- **Query historical GHI scores from completed assessments.** (1 connections) — `app/services/mttr_analyst.py`
- **Query audit events for finding lifecycle actions.** (1 connections) — `app/services/mttr_analyst.py`
- **Calculate Mean Time to Remediation from audit log timestamps. Groups events by…** (1 connections) — `app/services/mttr_analyst.py`
- **Determine if MTTR is improving, degrading, or stable.** (1 connections) — `app/services/mttr_analyst.py`
- **Calculate liability exposure in millions based on GHI score. Higher GHI → lower…** (1 connections) — `app/services/mttr_analyst.py`
- **Generates board-ready MTTR and risk-reduction analysis. Uses Gemini when…** (1 connections) — `app/services/mttr_analyst.py`
- *... and 8 more nodes in this community*

## Relationships

- [Organization](Organization.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [api/verification.py](api-verification.py.md) (2 shared connections)
- [main.py](main.py.md) (1 shared connections)

## Source Files

- `app/services/mttr_analyst.py`

## Audit Trail

- EXTRACTED: 59 (92%)
- INFERRED: 5 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*