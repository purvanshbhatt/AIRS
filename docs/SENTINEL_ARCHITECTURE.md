# Sentinel Architecture Document

## Overview
Sentinel is an advanced telemetry translation and simulation module integrated natively into the core ResilAI platform. It is engineered around a strict logic firewall: **Sentinel generates evidence. Core ResilAI calculates readiness.**

## Architectural Pipeline

1. **Splunk Enterprise (Ingestion Layer)**
   - **Path:** `app/integrations/splunk/`
   - Ingests SIEM logs via the Splunk MCP Server and Webhooks.

2. **Sentinel Evidence Engine**
   - **Path:** `app/sentinel/evidence/engine.py`
   - Normalizes raw JSON telemetry into typed `TelemetryEvent` structures.
   - Maps events to deterministic compliance controls using `app.sentinel.readiness.mapping`.

3. **Core AIRS Scoring Engine (The Arbiter)**
   - **Path:** `app/services/scoring.py` & `app/core/rubric.py`
   - Receives evidence from Sentinel and resolves all framework mappings (NIST, CIS, ISO).
   - Responsible for 100% of the mathematical tier calculations and scoring drops.

4. **Digital Twin (Zero-Mutation Simulator)**
   - **Path:** `app/sentinel/twin/engine.py`
   - Executes threat scenarios (e.g., Ransomware) by generating a deep-copied, in-memory replica of the latest `Assessment`.
   - Modifies the replica with missing controls and asks the core scoring engine to re-evaluate it.
   - Saves the Delta (the score impact) to `sentinel_simulations` without mutating production assessment data.

5. **Board Intelligence (Executive Output)**
   - **Path:** `app/sentinel/board_intelligence/generator.py`
   - Feeds the deterministic score drop and missing controls to Google Gemini (Flash 2.5).
   - Gemini translates the technical impact into a board-ready narrative, strictly constrained to avoid hallucinated scores or findings.
