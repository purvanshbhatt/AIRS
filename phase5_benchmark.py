import time
import os
import psutil
from datetime import datetime, timezone
import cProfile
import pstats
import io

from app.db.database import SessionLocal
from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
from app.services.clinic_engine.v2.readiness_engine import ReadinessEngine
from app.services.clinic_engine.v2.metrics_engine import MetricsEngine
from app.services.clinic_engine.v2.providers import ProviderRegistry
from app.services.clinic_engine.v2.schema import RawEvent

def generate_events(count: int):
    events = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        ms_event = RawEvent(
            event_type="microsoft.telemetry",
            source_system="microsoft",
            source_event_id=f"sync-ms-{i}",
            organization_id="default-org",
            payload={
                "entra_users": [
                    {
                        "user_id": f"u-{i}",
                        "user_principal_name": f"user{i}@clinic.com",
                        "mfa_enforced": i % 2 == 0,
                        "account_enabled": True,
                        "last_sign_in": (now).isoformat(),
                        "conditional_access_status": "enforced"
                    }
                ],
                "intune_devices": [
                    {
                        "device_id": f"d-{i}",
                        "device_name": f"PC-{i}",
                        "compliance_state": "compliant" if i % 2 == 0 else "noncompliant",
                        "bitlocker_status": "encrypted" if i % 2 == 0 else "not_encrypted",
                        "os_version": "10.0.19044"
                    }
                ],
                "defender_alerts": []
            }
        )
        events.append(ms_event)
    return events

def run_benchmark(event_count: int):
    events = generate_events(event_count)
    db = SessionLocal()
    org_id = "demo-org-123"
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024
    cpu_before = process.cpu_percent(interval=None)
    
    start_time = time.perf_counter()
    
    # Run the pipeline
    evidence = []
    for provider_cls in ProviderRegistry.list_all().values():
        evidence.extend(provider_cls.extract(events))
        
    engine = ClinicEvaluationEngine()
    moments = engine.evaluate(evidence)
    
    readiness_engine = ReadinessEngine(db)
    report = readiness_engine.evaluate(org_id, moments)
    
    metrics_engine = MetricsEngine(db)
    metrics_engine.record_daily_metrics(org_id, report)
    report.value = metrics_engine.get_summary(org_id, days=30)
    
    end_time = time.perf_counter()
    mem_after = process.memory_info().rss / 1024 / 1024
    cpu_after = process.cpu_percent(interval=None)
    
    latency_ms = (end_time - start_time) * 1000
    mem_used = mem_after - mem_before
    
    print(f"{event_count:5d} events | Latency: {latency_ms:7.2f} ms | Mem Used: {mem_used:6.2f} MB | CPU: {cpu_after:4.1f}%")
    db.close()

if __name__ == "__main__":
    print("Phase 5: Benchmarking")
    print("-" * 70)
    # Warm up CPU measurement
    psutil.Process(os.getpid()).cpu_percent(interval=0.1)
    
    for count in [100, 500, 1000, 5000]:
        run_benchmark(count)
        
    print("\nProfiling 1000 events for N+1 queries...")
    pr = cProfile.Profile()
    pr.enable()
    run_benchmark(1000)
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
    ps.print_stats(10) # Top 10 time consuming
    print(s.getvalue())
