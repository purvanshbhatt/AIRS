# ResilAI Architecture

## Overview
ResilAI is an AI-powered incident readiness platform designed to produce auditable readiness scores and executive-ready risk narratives.

The system is intentionally split into deterministic and generative components to preserve scoring integrity.

## Architecture Layers

### 1. Frontend
- Stack: React + Vite
- Responsibilities:
  - Assessment workflow and questionnaire UX
  - Readiness dashboards and posture visualization
  - Findings, recommendations, and report views

### 2. Backend API
- Stack: FastAPI
- Responsibilities:
  - Authentication and tenant-scoped access
  - Assessment lifecycle (create, answer, score, summarize)
  - Reporting and integration endpoints
  - Governance and reliability endpoints

### 3. Governance Scoring Engine
- Nature: deterministic, rules-based
- Responsibilities:
  - Convert control answers into weighted readiness scores
  - Map controls to NIST CSF 2.0 categories
  - Produce repeatable scoring outputs for audit and compliance

### 4. AI Narrative Layer
- Model: Gemini Flash
- Responsibilities:
  - Generate executive summaries and risk narratives
  - Translate scored findings into business-friendly language
  - Support board and investor communication

### 5. Cloud Infrastructure
- Runtime: Google Cloud Run
- Data: Firestore (persistent operational data)
- Deployment model:
  - Separate staging and demo/production deployment targets
  - Containerized backend with managed scaling
  - Hosted frontend with environment-specific builds

## Deterministic Scoring vs AI Narratives
ResilAI explicitly separates deterministic scoring from AI narrative generation.

### Why this separation matters
- Prevent hallucination-based risk scoring: AI cannot directly modify readiness score calculation.
- Preserve auditability: all scores are reproducible from explicit rules and answer inputs.
- Improve trust: executives receive AI-assisted explanation of risk, not AI-created risk metrics.
- Compliance alignment: deterministic controls map cleanly to governance frameworks.

In short, the scoring engine is the source of truth; AI is the interpretation layer.
