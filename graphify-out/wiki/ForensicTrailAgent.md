# ForensicTrailAgent

> 33 nodes · cohesion 0.10

## Key Concepts

- **ForensicTrailAgent** (12 connections) — `app/services/forensic_trail.py`
- **._generate_llm_trail()** (10 connections) — `app/services/forensic_trail.py`
- **AntigravityAgent** (8 connections) — `app/services/antigravity.py`
- **._generate_deterministic_trail()** (7 connections) — `app/services/forensic_trail.py`
- **.execute_remediation_agent()** (6 connections) — `app/services/antigravity.py`
- **search_vendor_documentation()** (6 connections) — `app/services/antigravity.py`
- **.execute_forensic_trail()** (6 connections) — `app/services/forensic_trail.py`
- **Any** (6 connections)
- **._compute_integrity_hash()** (5 connections) — `app/services/forensic_trail.py`
- **._generate_fallback_playbook()** (4 connections) — `app/services/antigravity.py`
- **._get_client()** (4 connections) — `app/services/antigravity.py`
- **._get_client()** (4 connections) — `app/services/forensic_trail.py`
- **._handle_siem_tool_call()** (4 connections) — `app/services/forensic_trail.py`
- **._match_siem_evidence()** (4 connections) — `app/services/forensic_trail.py`
- **.is_available()** (3 connections) — `app/services/antigravity.py`
- **.is_available()** (3 connections) — `app/services/forensic_trail.py`
- **query_siem_logs_sync()** (3 connections) — `app/services/forensic_trail.py`
- **.__init__()** (1 connections) — `app/services/antigravity.py`
- **Lazy-load Google Gemini client.** (1 connections) — `app/services/antigravity.py`
- **Executes the agentic loop to generate technical remediation steps.** (1 connections) — `app/services/antigravity.py`
- **Fallback playbook generator that uses the mock catalog locally.** (1 connections) — `app/services/antigravity.py`
- **Search the official vendor-specific technical guides to find configuration…** (1 connections) — `app/services/antigravity.py`
- **Orchestrates the Google Antigravity SDK Remediation Agent. Integrates Gemini…** (1 connections) — `app/services/antigravity.py`
- **.__init__()** (1 connections) — `app/services/forensic_trail.py`
- **Query raw SIEM logs for forensic trail generation. Args: siem_type: Which SIEM…** (1 connections) — `app/services/forensic_trail.py`
- *... and 8 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [main.py](main.py.md) (3 shared connections)
- [get_forensic_trail_agent](get_forensic_trail_agent.md) (1 shared connections)

## Source Files

- `app/services/antigravity.py`
- `app/services/forensic_trail.py`

## Audit Trail

- EXTRACTED: 56 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*