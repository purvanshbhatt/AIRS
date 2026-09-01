from fastapi import FastAPI
import uvicorn
import uuid

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "version": "9.1.0", "latency_ms": 12.5}

@app.post("/search")
def search(payload: dict):
    # Mock some Splunk events
    events = [
        {
            "id": str(uuid.uuid4()),
            "time": "2026-07-14T20:00:00Z",
            "source": "mock_splunk",
            "sourcetype": "mfa_logs",
            "host": "staging-auth",
            "raw": '{"severity": "high", "evidence_type": "splunk_alert", "message": "Suspicious login detected"}',
            "parsed_fields": {
                "severity": "high",
                "evidence_type": "splunk_alert",
                "message": "Suspicious login detected"
            }
        }
    ]
    return {
        "status": "success",
        "query": payload.get("query"),
        "total_count": 1,
        "events": events
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)
