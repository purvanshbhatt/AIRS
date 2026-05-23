# ResilAI - Quick Walkthrough

Estimated Review Time: 2 minutes

## What this project solves
Security teams monitor threats but struggle to measure actual incident readiness.

ResilAI measures incident readiness using deterministic governance scoring and translates technical findings into executive risk narratives using Gemini.

---

## Watch the demo (3 minutes)
Demo video:
https://youtu.be/Z_0aNizadoU

---

## Key Innovation
ResilAI separates deterministic risk scoring from AI narrative generation.

This architecture prevents AI hallucinations from affecting governance scoring.

---

## Technology Stack

Frontend:
React + Vite

Backend:
FastAPI

AI:
Gemini Flash via Google GenAI SDK

Infrastructure:
Google Cloud Run
Firestore

---

## Architecture

See the architecture diagram in README.md.

---

## Future Potential

ResilAI can integrate with SIEM tools like Splunk to automatically update readiness scores based on real-time security telemetry.

---

Thank you for reviewing ResilAI.
