# Architecture Decisions

ADR-001
Decision: Use deterministic scoring.
Reason: Enterprise trust. LLMs should not generate scores randomly.
Status: Permanent.

ADR-002
Decision: Gemini only generates narratives.
Reason: Prevents hallucination in critical security assessment data.
Status: Permanent.

ADR-003
Decision: Verification state system.
States: VERIFIED, PARTIAL, SELF_ATTESTED, UNVERIFIED
Status: Accepted.

ADR-004
Decision: SQLite Cache over Firestore
Reason: Firestore reads can be slow and expensive. The API synchronizes Firestore data into a local SQLite cache on startup for fast reads.
Status: Active.

ADR-005
Decision: Asynchronous Auto-Discovery
Reason: External API calls (Wazuh, Splunk) take longer than typical API timeout windows. Auto-discovery must run in the background.
Status: Active.
