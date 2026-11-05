# get_forensic_trail_agent

> 4 nodes · cohesion 0.50

## Key Concepts

- **get_forensic_trail_agent()** (7 connections) — `app/services/forensic_trail.py`
- **get_forensic_trail_agent()** (4 connections) — `app/services/antigravity.py`
- **Convenience re-export from forensic_trail module.** (1 connections) — `app/services/antigravity.py`
- **Get or create the singleton ForensicTrailAgent.** (1 connections) — `app/services/forensic_trail.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [api/verification.py](api-verification.py.md) (2 shared connections)
- [WazuhConfig](WazuhConfig.md) (1 shared connections)
- [ForensicTrailAgent](ForensicTrailAgent.md) (1 shared connections)
- [main.py](main.py.md) (1 shared connections)

## Source Files

- `app/services/antigravity.py`
- `app/services/forensic_trail.py`

## Audit Trail

- EXTRACTED: 9 (90%)
- INFERRED: 1 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*