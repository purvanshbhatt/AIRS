# ResilAI Technical Architecture

## Design Philosophy: Separation of Concerns
ResilAI is architected to solve the primary trust issue in AI-powered GRC: hallucinations. We utilize a three-tier isolation model:

### 1. Deterministic Scoring Engine (The Logic)
- Framework: FastAPI (Python 3.11+)
- Role: All risk math, NIST CSF 2.0 mappings, and GHI calculations are handled here.
- Validation: 79+ tests within our Internal Governance Validation Framework (IGVF) ensure zero-drift in scoring logic.

### 2. Encryption and Zero-Knowledge Vault (The Security)
- Standard: AES-256-GCM (Field-Level Encryption)
- Implementation: Sensitive organization metadata is encrypted before hitting Google Firestore.
- Privacy: Keys are managed via GCP Secret Manager, ensuring ResilAI remains a blind vault for customer-sensitive findings.

### 3. AI Intelligence Layer (The Narrative)
- Model: Google Gemini 1.5 Flash
- Role: Acts as a Live Agent to translate deterministic findings into multimodal executive narratives.
- Independence: Gemini never calculates the score; it only interprets the results provided by the Deterministic Engine.

## Google Cloud Infrastructure
- Compute: Google Cloud Run (Auto-scaling, Serverless)
- Storage: Google Firestore (Encrypted NoSQL)
- Deployment: CI/CD via automated PowerShell scripts with environment-specific isolation.
