# Hackathon Submission Guide

## Architecture Overview
The ResilAI platform serves as the canonical source of truth for organizational readiness. The **Sentinel module** operates natively within AIRS, ingesting operational telemetry via Splunk, converting it into deterministic evidence, and passing it to the core AIRS scoring engine. By maintaining this architectural boundary, we ensure a unified, enterprise-grade scoring methodology without duplicating code or creating parallel systems.

## Splunk Integration Overview
The integration lives in `app/integrations/splunk/`. It uses a custom-built Model Context Protocol (MCP) server to establish a secure link with a Splunk Enterprise instance. The Splunk connector streams high-priority security telemetry directly into the AIRS ingestion pipeline, acting as the primary trigger for the Agentic Operations showcase.

## Sentinel Workflow
1. **Telemetry Ingestion:** Sentinel receives raw security events (e.g., "failed_backup_validation") from Splunk.
2. **Deterministic Evidence:** The events are translated into standard `TelemetryEvidence` objects, mapped to specific compliance frameworks via `app.core.rubric.py`.
3. **Core Readiness Integration:** Evidence is submitted to the core AIRS engine.
4. **Digital Twin Simulation:** Sentinel executes a zero-mutation simulation (e.g., a Ransomware incident), asking the Core engine (`app.services.scoring.py`) to calculate the impact if missing controls were exploited.
5. **Board Intelligence:** Google Gemini parses the resulting score drop to produce an executive-ready response.

## Demo Flow
The hackathon demo is a seamless 3-minute flow:
1. **Trigger:** A critical system failure (e.g., EDR disabled) is logged in Splunk.
2. **Ingestion:** The Sentinel dashboard flashes as it processes the incoming Splunk webhook.
3. **Evidence Mapping:** The raw telemetry is instantly converted into missing control evidence.
4. **Simulation Execution:** The user triggers a "Ransomware Simulation" button.
5. **Executive Impact:** The screen visualizes the drop in organizational readiness (e.g., from 85.0 to 0.0) and generates an automated, board-ready narrative via Gemini.

## Judging Narrative
This submission addresses the classic cybersecurity problem: "What happens if this alert becomes a real incident?" Instead of just offering a dashboard of alerts, ResilAI Sentinel translates telemetry into business impact. By leveraging Splunk for data, the AIRS Core for deterministic scoring, and Google Gemini for executive narrative, we created an Agentic Operations platform that bridges the gap between the SOC and the Boardroom.

## Setup Instructions
1. Initialize the PostgreSQL Database and run `alembic upgrade head`.
2. Configure the `.env` file with `SPLUNK_HOST`, `SPLUNK_TOKEN`, and `GOOGLE_API_KEY`.
3. Boot the backend via `uvicorn app.main:app --reload`.
4. Run the demo script `python scripts/demo_sentinel.py` or trigger the webhook via Splunk.
