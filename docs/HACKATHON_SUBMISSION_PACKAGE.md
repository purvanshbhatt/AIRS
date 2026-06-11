# Hackathon Submission Package

This is the final checklist for the Agentic Operations hackathon submission.

## Repository & Links
* **Repository URL:** `[INSERT_GITHUB_URL]`
* **Demo Video URL:** `[INSERT_YOUTUBE_URL]`
* **Production Demo URL:** `[INSERT_PRODUCTION_APP_URL]`

## 1. Demo Video Checklist
- `[ ]` Introduce the problem: Security alerts lack business context.
- `[ ]` Show Splunk triggering a telemetry webhook.
- `[ ]` Show Sentinel processing the event into evidence.
- `[ ]` Trigger the "Digital Twin Ransomware Simulation".
- `[ ]` Highlight the 85.0 -> 0.0 deterministic score drop.
- `[ ]` Show the Gemini-generated executive board report.
- `[ ]` Conclude in exactly 3 minutes.

## 2. Architecture Checklist
- `[ ]` Architecture Diagram is embedded in the `README.md`.
- `[ ]` `SENTINEL_ARCHITECTURE.md` is included in the `/docs` folder.
- `[ ]` The logic firewall is clearly explained (Sentinel translates, Core scores).

## 3. Splunk Validation Checklist
- `[ ]` MCP Server is securely configured.
- `[ ]` Token and authentication secrets are verified as strictly out of the repository.
- `[ ]` Webhook ingestion handles the 3 required failure states (Backup, MFA, EDR).

## 4. MCP & Gemini Checklist
- `[ ]` `GOOGLE_API_KEY` operates successfully in the deployed environment.
- `[ ]` Gemini fallback deterministic templates trigger if the API rate limits during judging.

## 5. Final Submission Checklist
- `[ ]` Public Repository Audit completed (No secrets leaked).
- `[ ]` Automated Readiness Check (`scripts/hackathon_readiness_check.py`) passes 100%.
- `[ ]` `README.md` updated with "How to Run" instructions.
- `[ ]` Team members added to Devpost/Platform.
- `[ ]` Submit!
