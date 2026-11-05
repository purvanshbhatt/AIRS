I single-handedly built ResilAI (AIRS), an AI incident readiness platform that transforms raw security telemetry into deterministic readiness contracts. While existing GRC tools rely on subjective self-attestations or LLMs hallucinating risk scores, I architected a zero-trust deterministic evaluation engine across NIST CSF 2.0, NIST AI RMF, CIS Controls, and MITRE ATT&CK.

Key technical achievements:
1. Deterministic Engine & Invariants: Engineered an auditable math engine with 455+ passing unit/integration tests across 79 suites. Scores are cryptographically verifiable down to SHA-256 evidence hashes.
2. Logic Firewall: Implemented a pre-LLM deterministic defense layer intercepting poisoned retrieval patterns (MITRE AML.T0031) and prompt injections before context reaches Gemini.
3. 4-Tier Progressive Disclosure: Built a full-stack system (FastAPI on GCP Cloud Run + React/Vite/Tailwind) translating telemetry into 4 layers: Plain-English Executive Summary, Business/Liability Impact, Technical Evidence, and Cryptographic Provenance.

I independently engineered the backend pipelines, API contracts, and interactive frontend deployed live on Cloud Run and Firebase.