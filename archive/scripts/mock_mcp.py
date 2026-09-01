import asyncio, json, os
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "latency_ms": 12, "version": "1.0.0-mock"}

@app.post("/search")
async def search(req: Request):
    body = await req.json()
    q = (body.get("query") or "").lower()
    # Emit two telemetry rows whose parsed_fields include control_id matches
    if "mfa" in q:
        rows = [
            {"_time": "2026-07-16T15:00:00Z", "host": "dc01", "user": "alice", "action": "mfa_ok", "control_id": "IV-001", "severity": "low"},
            {"_time": "2026-07-16T15:01:00Z", "host": "dc01", "user": "bob",   "action": "mfa_ok", "control_id": "IV-001", "severity": "low"},
        ]
    elif "edr" in q:
        rows = [
            {"_time": "2026-07-16T15:00:00Z", "host": "wks01", "agent": "sentinel", "control_id": "DC-001", "severity": "low"},
        ]
    elif "drift" in q or "logging_health" in q:
        rows = [
            {"_time": "2026-07-16T15:00:00Z", "sourcetype": "resilai_drift", "control_id": "TL-002", "severity": "low"},
        ]
    else:
        rows = [
            {"_time": "2026-07-16T15:00:00Z", "source": "notable", "control_id": None, "severity": "info"},
        ]
    # Wrap rows in Splunk MCP canonical schema fields consumed by SplunkSearchResponse
    events = []
    search_id = q.replace(" ","")[:24] if q else "x"
    for i, r in enumerate(rows):
        events.append({
            "id": f"{search_id}-evt-{i}",
            "source": "mock",
            "sourcetype": "mfa_logs" if "mfa" in q else "edr_telemetry" if "edr" in q else "resilai_drift" if "drift" in q else "notable",
            "time": r["_time"],
            "host": r.get("host", "unknown"),
            "raw": json.dumps(r),
            "parsed_fields": {k: v for k, v in r.items() if k != "_time"},
        })
    return {"status": "ok", "events": events, "total_count": len(events)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("MOCK_MCP_PORT", "8766")), log_level="warning")
