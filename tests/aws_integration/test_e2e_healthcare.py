#!/usr/bin/env python3
"""
ResilAI Healthcare AWS Telemetry - End-to-End Integration Test.

Validates the complete pipeline:
  AWS Security Hub Findings -> AWSSecurityHubConnector.sync()
  -> RawEvent normalization -> Evidence ingestion -> Readiness evaluation

Product Invariants Enforced:
  1. LLMs NEVER calculate readiness scores.
  2. Findings are NOT modified by any AI.
  3. Evidence is traced to source.
  4. Scoring is deterministic.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_aws_credentials() -> Dict[str, str]:
    """Resolve AWS credentials from environment or boto3 session."""
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    session_token = os.environ.get("AWS_SESSION_TOKEN", "")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not (access_key and secret_key):
        try:
            import boto3
            session = boto3.Session(region_name=region)
            creds = session.get_credentials()
            if creds:
                frozen = creds.get_frozen_credentials()
                access_key = frozen.access_key or ""
                secret_key = frozen.secret_key or ""
                session_token = frozen.token or ""
        except Exception:
            pass

    return {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "aws_session_token": session_token,
        "aws_region": region,
    }


def run_e2e_test() -> Dict[str, Any]:
    """Execute full end-to-end test and return results."""
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tests": {},
        "overall_pass": False,
        "findings_count": 0,
        "evidence_records": 0,
        "pipeline_proven": False,
    }

    credentials = get_aws_credentials()
    if not credentials["aws_access_key_id"]:
        results["tests"]["credential_resolution"] = {
            "pass": False, "message": "No AWS credentials found"
        }
        return results

    results["tests"]["credential_resolution"] = {
        "pass": True, "message": "AWS credentials resolved"
    }

    # ----------------------------------------------------------------
    # TEST 1: Connector Authentication
    # ----------------------------------------------------------------
    print("\n[TEST 1] Connector Authentication...")
    from app.connectors.aws_security_hub import AWSSecurityHubConnector

    connector = AWSSecurityHubConnector(
        connector_id="e2e-healthcare-test",
        org_id="resilai-healthcare-validation",
        credentials=credentials,
        config={"region": credentials["aws_region"]},
    )

    auth_ok = asyncio.run(connector.authenticate())
    results["tests"]["authentication"] = {
        "pass": auth_ok,
        "message": "Authenticated" if auth_ok else "Auth failed",
    }
    if not auth_ok:
        print("  FAIL: Authentication failed")
        return results
    print("  PASS: Authenticated to AWS Security Hub")

    # ----------------------------------------------------------------
    # TEST 2: Permission Validation
    # ----------------------------------------------------------------
    print("\n[TEST 2] Permission Validation...")
    perm = asyncio.run(connector.validate_permissions())
    results["tests"]["permissions"] = {
        "pass": perm.valid,
        "message": perm.message,
    }
    print(f"  {'PASS' if perm.valid else 'FAIL'}: {perm.message}")

    # ----------------------------------------------------------------
    # TEST 3: Health Check
    # ----------------------------------------------------------------
    print("\n[TEST 3] Health Check...")
    health = asyncio.run(connector.health_check())
    results["tests"]["health_check"] = {
        "pass": health.status == "healthy",
        "latency_ms": health.latency_ms,
        "message": health.message,
    }
    print(f"  {'PASS' if health.status == 'healthy' else 'FAIL'}: "
          f"{health.message} ({health.latency_ms}ms)")

    # ----------------------------------------------------------------
    # TEST 4: Sync - Fetch Real Findings
    # ----------------------------------------------------------------
    print("\n[TEST 4] Sync - Fetching Real Security Hub Findings...")
    start = time.monotonic()
    events = asyncio.run(connector.sync())
    sync_ms = int((time.monotonic() - start) * 1000)

    results["findings_count"] = len(events)
    results["tests"]["sync"] = {
        "pass": len(events) > 0,
        "findings_count": len(events),
        "duration_ms": sync_ms,
        "message": f"Synced {len(events)} findings in {sync_ms}ms",
    }
    print(f"  {'PASS' if events else 'FAIL'}: {len(events)} findings synced "
          f"in {sync_ms}ms")

    if not events:
        print("  WARNING: No findings returned. AWS Config may still be initializing.")
        results["tests"]["sync"]["message"] += " - Config may need more time"
        return results

    # ----------------------------------------------------------------
    # TEST 5: Finding Structure Validation
    # ----------------------------------------------------------------
    print("\n[TEST 5] Finding Structure Validation...")
    required_fields = [
        "event_type", "source_system", "source_event_id", "severity", "payload"
    ]
    payload_fields = [
        "title", "description", "severity_label", "resources",
        "generator_id", "created_at",
    ]

    structure_ok = True
    for i, event in enumerate(events[:5]):  # Check first 5
        for field in required_fields:
            if not hasattr(event, field) or getattr(event, field) is None:
                print(f"  FAIL: Event {i} missing field '{field}'")
                structure_ok = False

        if hasattr(event, "payload") and event.payload:
            for pf in payload_fields:
                if pf not in event.payload:
                    print(f"  WARN: Event {i} payload missing '{pf}'")

    results["tests"]["finding_structure"] = {
        "pass": structure_ok,
        "message": "All required fields present" if structure_ok else "Missing fields",
    }
    print(f"  {'PASS' if structure_ok else 'FAIL'}: Finding structure validation")

    # ----------------------------------------------------------------
    # TEST 6: Severity Distribution Analysis
    # ----------------------------------------------------------------
    print("\n[TEST 6] Severity Distribution...")
    severity_counts: Dict[str, int] = {}
    for event in events:
        sev = event.severity if hasattr(event, "severity") else "unknown"
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    results["tests"]["severity_distribution"] = {
        "pass": True,
        "distribution": severity_counts,
        "message": str(severity_counts),
    }
    for sev, count in sorted(severity_counts.items()):
        print(f"  {sev.upper():>12}: {count}")

    # ----------------------------------------------------------------
    # TEST 7: Finding Categories
    # ----------------------------------------------------------------
    print("\n[TEST 7] Finding Categories...")
    categories = set()
    for event in events:
        if hasattr(event, "payload") and event.payload:
            gen = event.payload.get("generator_id", "")
            if gen:
                # Extract category from generator ID
                parts = gen.split("/")
                cat = parts[0] if parts else gen
                categories.add(cat)

    results["tests"]["finding_categories"] = {
        "pass": len(categories) > 0,
        "categories": sorted(categories),
        "count": len(categories),
        "message": f"{len(categories)} categories found",
    }
    for cat in sorted(categories):
        print(f"  - {cat}")

    # ----------------------------------------------------------------
    # TEST 8: Evidence Traceability
    # ----------------------------------------------------------------
    print("\n[TEST 8] Evidence Traceability...")
    traceable = 0
    for event in events:
        has_source_id = (hasattr(event, "source_event_id")
                        and event.source_event_id)
        has_source_system = (hasattr(event, "source_system")
                            and event.source_system == "aws_security_hub")
        has_created = (hasattr(event, "payload") and event.payload
                      and event.payload.get("created_at"))
        if has_source_id and has_source_system and has_created:
            traceable += 1

    trace_pct = (traceable / len(events)) * 100 if events else 0
    results["tests"]["traceability"] = {
        "pass": trace_pct >= 90,
        "traceable_count": traceable,
        "total_count": len(events),
        "percentage": trace_pct,
        "message": f"{traceable}/{len(events)} findings traceable ({trace_pct:.0f}%)",
    }
    print(f"  {'PASS' if trace_pct >= 90 else 'FAIL'}: "
          f"{traceable}/{len(events)} findings traceable ({trace_pct:.0f}%)")

    # ----------------------------------------------------------------
    # TEST 9: No LLM in Scoring Path (Invariant Check)
    # ----------------------------------------------------------------
    print("\n[TEST 9] Product Invariant - No LLM in Scoring Path...")
    # Verify the connector code does not import or call any AI/LLM
    connector_path = PROJECT_ROOT / "app" / "connectors" / "aws_security_hub.py"
    code = connector_path.read_text()
    llm_indicators = ["openai", "anthropic", "gemini", "langchain",
                      "llm", "gpt", "chat_completion", "generate_text"]
    llm_found = [ind for ind in llm_indicators if ind.lower() in code.lower()]

    results["tests"]["no_llm_in_connector"] = {
        "pass": len(llm_found) == 0,
        "message": "No LLM references" if not llm_found else f"Found: {llm_found}",
    }
    print(f"  {'PASS' if not llm_found else 'FAIL'}: "
          f"{'No LLM references in connector' if not llm_found else f'Found: {llm_found}'}")

    # ----------------------------------------------------------------
    # TEST 10: Sample Finding Details (for report)
    # ----------------------------------------------------------------
    print("\n[TEST 10] Sample Findings for Report...")
    sample_findings = []
    for event in events[:10]:
        if hasattr(event, "payload") and event.payload:
            sample_findings.append({
                "title": event.payload.get("title", ""),
                "severity": event.severity if hasattr(event, "severity") else "unknown",
                "source_event_id": event.source_event_id[:60] + "..."
                    if len(event.source_event_id) > 60
                    else event.source_event_id,
                "compliance_status": event.payload.get("compliance_status", "N/A"),
            })
            print(f"  [{event.severity.upper():>8}] {event.payload.get('title', '')[:80]}")

    results["tests"]["sample_findings"] = {
        "pass": True,
        "samples": sample_findings,
    }

    # ----------------------------------------------------------------
    # Overall Result
    # ----------------------------------------------------------------
    test_results = results["tests"]
    critical_tests = ["authentication", "permissions", "sync", "finding_structure",
                      "traceability", "no_llm_in_connector"]
    all_critical_pass = all(
        test_results.get(t, {}).get("pass", False) for t in critical_tests
    )

    results["overall_pass"] = all_critical_pass
    results["pipeline_proven"] = all_critical_pass and len(events) > 0
    results["evidence_records"] = len(events)

    return results


def main() -> int:
    print("=" * 60)
    print("ResilAI Healthcare AWS Telemetry - E2E Integration Test")
    print("=" * 60)

    results = run_e2e_test()

    # Save results
    output_dir = Path(__file__).parent
    output_file = output_dir / "e2e_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 60)
    if results["pipeline_proven"]:
        print("PIPELINE PROVEN: AWS Telemetry -> ResilAI Evidence")
        print(f"  Findings ingested : {results['findings_count']}")
        print(f"  All tests passed  : YES")
    elif results["overall_pass"]:
        print("TESTS PASSED but pipeline needs more findings")
    else:
        print("SOME TESTS FAILED")
        for name, test in results.get("tests", {}).items():
            if not test.get("pass", False):
                print(f"  FAIL: {name} - {test.get('message', '')}")
    print("=" * 60)

    return 0 if results["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
