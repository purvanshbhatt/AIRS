# download_report

> 15 nodes · cohesion 0.23

## Key Concepts

- **download_report()** (10 connections) — `app/api/reports.py`
- **get_report_service()** (10 connections) — `app/api/reports.py`
- **list_reports()** (9 connections) — `app/api/reports.py`
- **get_report()** (7 connections) — `app/api/reports.py`
- **delete_report()** (6 connections) — `app/api/reports.py`
- **Session** (5 connections)
- **User** (5 connections)
- **get** (3 connections)
- **datetime** (2 connections)
- **delete** (1 connections)
- **ReportType** (1 connections)
- **Get report with full snapshot data.** (1 connections) — `app/api/reports.py`
- **Download report as PDF.** (1 connections) — `app/api/reports.py`
- **Get report service with tenant isolation.** (1 connections) — `app/api/reports.py`
- **List reports owned by the current user.** (1 connections) — `app/api/reports.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (6 shared connections)
- [User](User.md) (5 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [main.py](main.py.md) (1 shared connections)
- [ProfessionalPDFGenerator](ProfessionalPDFGenerator.md) (1 shared connections)
- [organizations.py](organizations.py.md) (1 shared connections)

## Source Files

- `app/api/reports.py`

## Audit Trail

- EXTRACTED: 33 (85%)
- INFERRED: 6 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*