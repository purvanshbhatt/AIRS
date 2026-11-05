# MetricsEngine

> 19 nodes · cohesion 0.14

## Key Concepts

- **MetricsEngine** (12 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **phase5_benchmark.py** (12 connections) — `phase5_benchmark.py`
- **ClinicValueMetric** (8 connections) — `app/models/clinic/value_metric.py`
- **metrics_engine.py** (8 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **run_benchmark()** (7 connections) — `phase5_benchmark.py`
- **ValueSummary** (5 connections) — `app/services/clinic_engine/v2/contracts.py`
- **.record_daily_metrics()** (4 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **.get_summary()** (3 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **generate_events()** (3 connections) — `phase5_benchmark.py`
- **.__init__()** (2 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **Base** (1 connections)
- **Clinic value metric model.** (1 connections) — `app/models/clinic/value_metric.py`
- **Business value delivered. These are what convince customers to renew.** (1 connections) — `app/services/clinic_engine/v2/contracts.py`
- **DailyReadinessReport** (1 connections)
- **Session** (1 connections)
- **The Value Layer Engine. Tracks the tangible business value delivered to the…** (1 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **Record the value delivered for today based on the readiness report.** (1 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **Aggregate metrics over the last N days.** (1 connections) — `app/services/clinic_engine/v2/metrics_engine.py`
- **ValueSummary** (1 connections)

## Relationships

- [contracts.py](contracts.py.md) (7 shared connections)
- [router.py](router.py.md) (4 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [EvidenceKind](EvidenceKind.md) (3 shared connections)
- [Evidence](Evidence.md) (2 shared connections)
- [schema.py](schema.py.md) (2 shared connections)
- [PilotService](PilotService.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)
- [SessionLocal](SessionLocal.md) (1 shared connections)

## Source Files

- `app/models/clinic/value_metric.py`
- `app/services/clinic_engine/v2/contracts.py`
- `app/services/clinic_engine/v2/metrics_engine.py`
- `phase5_benchmark.py`

## Audit Trail

- EXTRACTED: 44 (90%)
- INFERRED: 5 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*