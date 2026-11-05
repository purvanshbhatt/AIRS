# Splunk Hackathon Demo Flow

This document details the exact technical flow demonstrated in the Hackathon submission video.

## Sequence of Events

**1. The Splunk Trigger**
* A critical alert fires in Splunk Enterprise indicating that the Multi-Factor Authentication (MFA) enforcement policy was disabled on the domain controller.
* **Flow:** `Splunk` → `POST /api/sentinel/integrations/splunk` → `Telemetry`

**2. Deterministic Evidence Translation**
* Sentinel intercepts the webhook and processes the event.
* **Flow:** `Telemetry` → `app/sentinel/evidence/engine.py` → `Evidence`
* *Result:* The telemetry is mapped to a missing Identity & Access Management control (`iv_01`).

**3. Core AIRS Scoring Evaluation**
* Sentinel queries the core platform for the dynamic framework mapping of the missing control.
* **Flow:** `Evidence` → `app/core/rubric.py` → `Core AIRS Scoring`

**4. The Digital Twin Execution**
* The user clicks "Simulate Ransomware Incident".
* **Flow:** `Core AIRS Scoring` → `app/sentinel/twin/engine.py` → `Digital Twin`
* *Result:* An in-memory Assessment replica is subjected to the missing MFA control. The score drops from 85.0 to 35.0.

**5. Board Intelligence Generation**
* Sentinel compiles the data and requests an executive summary.
* **Flow:** `Digital Twin` → `app/sentinel/board_intelligence/generator.py` → `Board Intelligence`
* *Result:* Gemini outputs a 3-sentence executive narrative explaining the 50-point drop in readiness due to the MFA failure, ready for presentation.
