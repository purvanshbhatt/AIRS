# ResilAI Security Design

ResilAI is designed for high-trust security analytics, where scoring integrity and tenant isolation are mandatory.

## Core Security Design Decisions

### 1. Separation of Scoring Engine and AI
- Deterministic scoring logic computes all readiness metrics.
- Gemini Flash is restricted to narrative generation and explanation.
- This prevents hallucination-based scoring and preserves auditability.

### 2. Encrypted Configuration Storage
- Sensitive configuration is managed through secure environment handling and cloud secret management patterns.
- Production-facing credentials and secrets are not hard-coded in application logic.
- Runtime configuration is isolated by deployment environment.

### 3. Cloud-Native Deployment Security
- Backend services run on Google Cloud Run with managed runtime hardening.
- Firestore is used for managed persistence with cloud IAM controls.
- Separate staging and demo/production deployments reduce accidental cross-environment impact.

### 4. Least Privilege Architecture
- Access is scoped by authenticated identity and tenant ownership boundaries.
- Data access paths are designed to enforce ownership checks.
- Service-level responsibilities are separated to minimize blast radius.

## Security Posture Principles
- Determinism for trust
- Isolation for tenant safety
- Managed cloud controls for operational resilience
- Explicit governance mappings for compliance readiness
