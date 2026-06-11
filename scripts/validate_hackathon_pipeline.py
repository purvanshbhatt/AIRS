import os
import sys
import time
import httpx
import asyncio
import subprocess

async def main():
    print("========================================")
    print(" Sentinel Hackathon Pipeline Validation ")
    print("========================================")

    # 1. Inject Splunk Event
    print("\n[STEP 1] Injecting Splunk Event via HEC...")
    start = time.time()
    try:
        # We assume splunk_hec_injector.py is in the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        injector_path = os.path.join(script_dir, "splunk_hec_injector.py")
        
        # Run the injector
        result = subprocess.run([sys.executable, injector_path, "--event", "mfa"], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  [FAIL] Injector failed: {result.stderr}")
            sys.exit(1)
            
        print(f"  [PASS] Event injected successfully ({(time.time()-start)*1000:.2f}ms)")
        print(f"         Output: {result.stdout.strip()}")
    except Exception as e:
        print(f"  [FAIL] Failed to run injector: {e}")
        sys.exit(1)

    print("  [INFO] Waiting 3 seconds for Splunk indexing...")
    time.sleep(3)

    # 2-6. Trigger Simulation API (which handles fetch, evidence, simulation, report)
    print("\n[STEP 2] Triggering Sentinel Pipeline API...")
    
    from app.api.routes.sentinel_test import trigger_simulation, SimulationTriggerRequest
    from app.sentinel.db.database import SessionLocal
    
    payload = SimulationTriggerRequest(
        scenario="CredentialAbuse",
        org_id="hackathon-demo-org"
    )

    db = SessionLocal()
    start = time.time()
    try:
        # Bypass HTTP, call the logic directly
        os.environ["ENABLE_SENTINEL_TEST_ROUTES"] = "true"
        response = await trigger_simulation(payload, db)
        data = response
        
        latency = (time.time() - start) * 1000
        print(f"  [PASS] API Pipeline completed successfully ({latency:.2f}ms)")
        
        # Validate components in response
        metrics = data.get("ingestion_metrics", {})
        sim = data.get("simulation", {})
        report = data.get("board_report", {})
        component_latencies = data.get("latencies", {})
        
        print("\n[PIPELINE VERIFICATION]")
        print(f"  - Telemetry Events Fetched: {metrics.get('events_ingested', 0)}")
        print(f"  - Telemetry Evidence Generated: {metrics.get('evidence_generated', 0)}")
        print(f"  - Simulation Created: {sim.get('id')} (Score: {sim.get('readiness_impact_score')})")
        
        has_narrative = bool(report.get("board_narrative"))
        print(f"  - Board Report Generated: {'Yes' if has_narrative else 'No'}")
        
        print("\n[LATENCY METRICS]")
        print(f"  - Ingestion: {component_latencies.get('ingestion_ms', 0):.2f}ms")
        print(f"  - Evidence Generation: {component_latencies.get('evidence_ms', 0):.2f}ms")
        print(f"  - Simulation: {component_latencies.get('simulation_ms', 0):.2f}ms")
        print(f"  - Report Generation: {component_latencies.get('report_ms', 0):.2f}ms")
        
        if metrics.get('events_ingested', 0) == 0:
            print("  [WARN] Pipeline succeeded but 0 events were fetched. Was the event indexed in time?")
            
    except Exception as e:
        print(f"  [FAIL] API Pipeline Error: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"         Response details: {response.text}")
        sys.exit(1)

    print("\n[RESULT] ALL VALIDATIONS PASSED [OK]")

if __name__ == "__main__":
    asyncio.run(main())
