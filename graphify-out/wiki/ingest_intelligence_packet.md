# ingest_intelligence_packet

> 16 nodes · cohesion 0.15

## Key Concepts

- **ingest_intelligence_packet()** (11 connections) — `app/api/intelligence.py`
- **intelligence_packet.py** (7 connections) — `app/schemas/intelligence_packet.py`
- **ResilAIIntelligencePacket** (6 connections) — `app/schemas/intelligence_packet.py`
- **IntelligencePacketIngestResponse** (4 connections) — `app/schemas/intelligence_packet.py`
- **RemediationLedgerItem** (3 connections) — `app/schemas/intelligence_packet.py`
- **._validate_ledger()** (3 connections) — `app/schemas/intelligence_packet.py`
- **SimulationPayload** (3 connections) — `app/schemas/intelligence_packet.py`
- **field_validator** (2 connections)
- **SimulationImpactAnalysis** (2 connections) — `app/schemas/intelligence_packet.py`
- **._non_empty_lists()** (2 connections) — `app/schemas/intelligence_packet.py`
- **post** (1 connections)
- **Session** (1 connections)
- **User** (1 connections)
- **Validate Gemini JSON contract and persist remediation tasks to Firestore.…** (1 connections) — `app/api/intelligence.py`
- **Strict JSON contract for Gemini intelligence packets.** (1 connections) — `app/schemas/intelligence_packet.py`
- **Unified intelligence contract consumed by the frontend. This is intentionally…** (1 connections) — `app/schemas/intelligence_packet.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (5 shared connections)
- [BaseModel](BaseModel.md) (5 shared connections)
- [get_firestore_client](get_firestore_client.md) (2 shared connections)
- [User](User.md) (1 shared connections)

## Source Files

- `app/api/intelligence.py`
- `app/schemas/intelligence_packet.py`

## Audit Trail

- EXTRACTED: 27 (87%)
- INFERRED: 4 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*