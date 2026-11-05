import json
from fastapi.testclient import TestClient
from app.main import app

def recursive_remove(obj, keys_to_remove):
    if isinstance(obj, dict):
        for key in keys_to_remove:
            obj.pop(key, None)
        for key, value in obj.items():
            recursive_remove(value, keys_to_remove)
    elif isinstance(obj, list):
        for item in obj:
            recursive_remove(item, keys_to_remove)

def normalize_payload(payload: dict) -> str:
    """Removes dynamic UUIDs and Timestamps before comparison."""
    p = json.loads(json.dumps(payload))
    recursive_remove(p, ["report_id", "generated_at", "audit_snapshot_id", "last_verified_at"])
    
    # We should also sort any list of dictionaries to ensure deterministic order
    # if order isn't guaranteed by the engine (e.g. iterating over DB results)
    def sort_lists(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = sort_lists(v)
        elif isinstance(obj, list):
            # Try to sort the list if it's a list of dicts with 'name' or 'label'
            try:
                obj = sorted([sort_lists(item) for item in obj], key=lambda x: str(x))
            except TypeError:
                pass
        return obj

    p = sort_lists(p)
    
    return json.dumps(p, sort_keys=True)

def run_deterministic():
    print("Phase 4: Deterministic Verification")
    client = TestClient(app)
    org_id = "demo-org-123"
    
    resp = client.post("/internal/pilot/seed")
    
    baseline = None
    for i in range(5):
        resp = client.get(f"/api/clinic/readiness/{org_id}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        normalized = normalize_payload(resp.json())
        if baseline is None:
            baseline = normalized
            print("Baseline generated.")
        else:
            if normalized != baseline:
                # To help debug, print where it diverged
                import difflib
                diff = list(difflib.context_diff(
                    baseline.splitlines(),
                    normalized.splitlines(),
                    fromfile='baseline',
                    tofile='current'
                ))
                print("\n".join(diff))
                assert False, f"Run {i+1} diverged from baseline!"
            else:
                print(f"Run {i+1} matches baseline.")
            
    print("All deterministic verification tests passed!")

if __name__ == "__main__":
    run_deterministic()
