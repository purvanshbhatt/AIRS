# _build_summary_payload

> 10 nodes · cohesion 0.24

## Key Concepts

- **_build_summary_payload()** (8 connections) — `app/api/v1/reports.py`
- **download_board_story_pdf()** (8 connections) — `app/api/v1/reports.py`
- **get_board_story()** (8 connections) — `app/api/v1/reports.py`
- **get** (2 connections)
- **Session** (2 connections)
- **Assessment** (1 connections)
- **Organization** (1 connections)
- **Build a scoring-snapshot-sourced payload. All numbers trace to the DB record.** (1 connections) — `app/api/v1/reports.py`
- **Get the Board Story (Executive Narrative + Roadmap) as structured JSON for an…** (1 connections) — `app/api/v1/reports.py`
- **Server-side PDF generation for the Board Story. All numbers embedded in the PDF…** (1 connections) — `app/api/v1/reports.py`

## Relationships

- [Organization](Organization.md) (6 shared connections)
- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [generate_board_story](generate_board_story.md) (2 shared connections)

## Source Files

- `app/api/v1/reports.py`

## Audit Trail

- EXTRACTED: 16 (73%)
- INFERRED: 6 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*