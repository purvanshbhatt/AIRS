"""
Empirical Adversarial Concurrency & Stress Testing for Public Product Config API.

Target: Milestone 1 (Host- and Route-Aware Vertical Architecture)
Endpoint: GET /api/public/product-config
Scope:
- High-concurrency async load (100 simultaneous requests) with varied headers/params
- Multi-threaded concurrency with ThreadPoolExecutor
- Precedence conflict isolation under concurrent load
- Malformed inputs, fuzzing, and extreme values under concurrency
- Latency and zero-regression benchmarking
"""

import asyncio
import concurrent.futures
import random
import time
from typing import Dict, Any, Tuple
import pytest
import httpx
from starlette.testclient import TestClient
from app.main import app
from app.api.public import resolve_vertical_key, VERTICAL_CONFIGS


def test_concurrent_async_requests_high_load():
    """Execute 100 concurrent async requests with varied query params, headers, and hostnames.
    
    Verifies that all 100 requests succeed (HTTP 200), return valid schema data,
    and accurately resolve the expected vertical according to precedence rules.
    """
    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Generate 100 test cases with varied parameters
            test_cases = []
            for i in range(100):
                case_type = i % 5
                if case_type == 0:
                    # Healthcare via query param
                    test_cases.append({
                        "params": {"vertical": "healthcare"},
                        "headers": {},
                        "expected": "healthcare",
                    })
                elif case_type == 1:
                    # Legal via query param
                    test_cases.append({
                        "params": {"vertical": "legal"},
                        "headers": {"X-ResilAI-Vertical": "healthcare"}, # Query should override header
                        "expected": "legal",
                    })
                elif case_type == 2:
                    # Healthcare via header
                    test_cases.append({
                        "params": {},
                        "headers": {"X-ResilAI-Vertical": "healthcare", "Host": "legal.staging.resilai.org"},
                        "expected": "healthcare", # Header should override host
                    })
                elif case_type == 3:
                    # Legal via subdomain
                    test_cases.append({
                        "params": {},
                        "headers": {"Host": "legal.staging.resilai.org"},
                        "expected": "legal",
                    })
                else:
                    # Default / general
                    test_cases.append({
                        "params": {},
                        "headers": {"Host": "staging.resilai.org"},
                        "expected": "general",
                    })

            # Shuffle to maximize concurrent diversity
            random.shuffle(test_cases)

            async def fetch_case(tc: Dict[str, Any]) -> Tuple[int, Dict[str, Any], str]:
                res = await client.get(
                    "/api/public/product-config",
                    params=tc["params"],
                    headers=tc["headers"],
                )
                return res.status_code, res.json(), tc["expected"]

            start_time = time.perf_counter()
            results = await asyncio.gather(*(fetch_case(tc) for tc in test_cases))
            elapsed = time.perf_counter() - start_time

            assert len(results) == 100
            for status_code, body, expected_key in results:
                assert status_code == 200, f"Expected 200 but got {status_code}: {body}"
                assert body["vertical_key"] == expected_key, f"Expected {expected_key} but got {body['vertical_key']}"
                assert body["demo_org_id"] == VERTICAL_CONFIGS[expected_key]["demo_org_id"]
                assert body["display_name"] == VERTICAL_CONFIGS[expected_key]["display_name"]
                assert isinstance(body["focus_areas"], list)
                assert len(body["focus_areas"]) > 0

            # High throughput verification (all 100 in-memory requests should complete rapidly)
            assert elapsed < 5.0, f"100 concurrent requests took too long: {elapsed:.2f}s"

    asyncio.run(_run())


def test_multithreaded_concurrency_stress():
    """Execute 50 concurrent requests across 10 OS threads using ThreadPoolExecutor and TestClient."""
    client = TestClient(app)

    tasks = []
    for i in range(50):
        if i % 3 == 0:
            tasks.append(("/api/public/product-config?vertical=healthcare", {}, "healthcare"))
        elif i % 3 == 1:
            tasks.append(("/api/public/product-config", {"X-ResilAI-Vertical": "legal"}, "legal"))
        else:
            tasks.append(("/api/public/product-config", {"Host": "general.staging.resilai.org"}, "general"))

    def worker(task):
        url, headers, expected_vertical = task
        res = client.get(url, headers=headers)
        return res.status_code, res.json(), expected_vertical

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, t) for t in tasks]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 50
    for status_code, body, expected_vertical in results:
        assert status_code == 200
        assert body["vertical_key"] == expected_vertical
        assert body["demo_org_id"] == VERTICAL_CONFIGS[expected_vertical]["demo_org_id"]


def test_concurrency_precedence_conflict_stress():
    """Stress test precedence under 60 concurrent requests with conflicting indicators.
    
    Query (?vertical=healthcare) vs Header (X-ResilAI-Vertical: legal) vs Host (legal.staging.resilai.org).
    Query parameter MUST win 100% of the time with 0 cross-request leaks.
    """
    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            async def send_conflict(vertical_target: str, header_conflict: str, host_conflict: str):
                res = await client.get(
                    f"/api/public/product-config?vertical={vertical_target}",
                    headers={
                        "X-ResilAI-Vertical": header_conflict,
                        "Host": host_conflict,
                    },
                )
                return res.status_code, res.json()

            coros = []
            for i in range(60):
                if i % 2 == 0:
                    coros.append(send_conflict("healthcare", "legal", "legal.staging.resilai.org"))
                else:
                    coros.append(send_conflict("legal", "healthcare", "healthcare.staging.resilai.org"))

            results = await asyncio.gather(*coros)

            for i, (status, data) in enumerate(results):
                expected = "healthcare" if (i % 2 == 0) else "legal"
                assert status == 200
                assert data["vertical_key"] == expected, f"Precedence failed on iteration {i}: got {data['vertical_key']}"

    asyncio.run(_run())


def test_concurrent_fuzzing_and_malformed_inputs():
    """Fuzz endpoint with 50 concurrent malformed inputs (unicode, massive strings, SQL-like syntax).
    
    Endpoint must safely fall back to 'general' without 500 errors or unhandled exceptions.
    """
    query_fuzz = [
        "   ",
        "../../etc/passwd",
        "<script>alert(1)</script>",
        "' OR '1'='1",
        "医療", # Japanese for medical (URL encoded query param)
        "juridique", # French for legal
        "A" * 5000, # Large payload
        "health care", # Space separated
        "legal?vertical=healthcare", # Nested query
        "__proto__",
        "constructor",
    ]

    header_fuzz = [
        "   ",
        "../../etc/passwd",
        "<script>alert(1)</script>",
        "' OR '1'='1",
        "unknown-header",
        "juridique",
        "A" * 500,
        "health care",
        "__proto__",
    ]

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            async def send_fuzz(q_val: str, h_val: str):
                res = await client.get(
                    "/api/public/product-config",
                    params={"vertical": q_val},
                    headers={"X-ResilAI-Vertical": h_val},
                )
                return res.status_code, res.json()

            # Repeat fuzz items to 50 concurrent requests
            coros = [
                send_fuzz(
                    query_fuzz[i % len(query_fuzz)],
                    header_fuzz[i % len(header_fuzz)],
                )
                for i in range(50)
            ]
            results = await asyncio.gather(*coros)

            for status, data in results:
                assert status == 200, f"Fuzzing resulted in status {status}: {data}"
                # All unmapped values must safely default to general
                assert data["vertical_key"] == "general"
                assert data["demo_org_id"] == "demo-acme-technologies"

    asyncio.run(_run())


def test_concurrent_latency_benchmark():
    """Verify latency remains sub-25ms per request under concurrent load of 50 requests."""
    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            start_time = time.perf_counter()
            coros = [
                client.get("/api/public/product-config?vertical=healthcare")
                for _ in range(50)
            ]
            responses = await asyncio.gather(*coros)
            total_time = time.perf_counter() - start_time

            avg_latency_ms = (total_time / 50) * 1000

            for r in responses:
                assert r.status_code == 200

            # In-memory retrieval should average well under 25ms per request in async batch
            assert avg_latency_ms < 25.0, f"Average latency too high: {avg_latency_ms:.2f}ms"

    asyncio.run(_run())

