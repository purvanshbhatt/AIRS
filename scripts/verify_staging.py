"""
Live Staging Verification Script for ResilAI (AIRS)
Performs live E2E integration testing against Cloud Run backend and Firebase Hosting staging targets.
"""

import sys
import json
import time
import urllib.request
import urllib.error

FRONTEND_STAGING_URL = "https://airs-staging-0384513977.web.app"
BACKEND_STAGING_URL = "https://airs-api-staging-knu3wsxymq-uc.a.run.app"

results = []

def log_result(test_name, success, details):
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {test_name}: {details}")
    results.append({
        "test": test_name,
        "success": success,
        "details": details
    })

def test_frontend_access():
    start_time = time.time()
    try:
        req = urllib.request.Request(FRONTEND_STAGING_URL, headers={"User-Agent": "AIRS-Staging-Tester/1.0"})
        with urllib.request.urlopen(req) as resp:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            code = resp.getcode()
            headers = dict(resp.headers)
            body = resp.read().decode('utf-8')
            
            robots_tag = headers.get("X-Robots-Tag", headers.get("x-robots-tag", "N/A"))
            has_root_div = '<div id="root">' in body
            
            success = (code == 200) and has_root_div
            log_result("1. Frontend Staging Accessibility", success,
                       f"Status={code}, Latency={latency_ms}ms, Robots={robots_tag}, RootDiv={has_root_div}")
            return {
                "status": code,
                "latency_ms": latency_ms,
                "robots_tag": robots_tag,
                "has_root_div": has_root_div
            }
    except Exception as e:
        log_result("1. Frontend Staging Accessibility", False, str(e))
        return None

def test_backend_health():
    start_time = time.time()
    try:
        url = f"{BACKEND_STAGING_URL}/health"
        req = urllib.request.Request(url, headers={"User-Agent": "AIRS-Staging-Tester/1.0"})
        with urllib.request.urlopen(req) as resp:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            code = resp.getcode()
            body_json = json.loads(resp.read().decode('utf-8'))
            
            success = (code == 200) and (body_json.get("status") == "ok")
            log_result("2. Backend Health Check (/health)", success,
                       f"Status={code}, Latency={latency_ms}ms, Body={body_json}")
            return {
                "status": code,
                "latency_ms": latency_ms,
                "body": body_json
            }
    except Exception as e:
        log_result("2. Backend Health Check (/health)", False, str(e))
        return None

def test_backend_config():
    start_time = time.time()
    try:
        url = f"{BACKEND_STAGING_URL}/api/v1/config"
        req = urllib.request.Request(url, headers={"User-Agent": "AIRS-Staging-Tester/1.0"})
        with urllib.request.urlopen(req) as resp:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            code = resp.getcode()
            body_json = json.loads(resp.read().decode('utf-8'))
            
            env = body_json.get("environment")
            api_base = body_json.get("api_base_url")
            auth_provider = body_json.get("auth_provider")
            
            success = (code == 200) and (env == "staging") and (auth_provider == "firebase")
            log_result("3. Environment Config Endpoint (/api/v1/config)", success,
                       f"Status={code}, Latency={latency_ms}ms, Env={env}, ApiBase={api_base}, AuthProvider={auth_provider}")
            return {
                "status": code,
                "latency_ms": latency_ms,
                "environment": env,
                "api_base_url": api_base,
                "auth_provider": auth_provider
            }
    except Exception as e:
        log_result("3. Environment Config Endpoint (/api/v1/config)", False, str(e))
        return None

def test_cors_preflight():
    start_time = time.time()
    try:
        url = f"{BACKEND_STAGING_URL}/api/v1/config"
        req = urllib.request.Request(
            url,
            method="OPTIONS",
            headers={
                "User-Agent": "AIRS-Staging-Tester/1.0",
                "Origin": FRONTEND_STAGING_URL,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            }
        )
        with urllib.request.urlopen(req) as resp:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            code = resp.getcode()
            headers = dict(resp.headers)
            
            allow_origin = headers.get("Access-Control-Allow-Origin", headers.get("access-control-allow-origin", "N/A"))
            allow_creds = headers.get("Access-Control-Allow-Credentials", headers.get("access-control-allow-credentials", "N/A"))
            
            success = (code in [200, 204]) and (allow_origin == FRONTEND_STAGING_URL)
            log_result("4. CORS Preflight Check (OPTIONS)", success,
                       f"Status={code}, Latency={latency_ms}ms, AllowOrigin={allow_origin}, AllowCreds={allow_creds}")
            return {
                "status": code,
                "latency_ms": latency_ms,
                "allow_origin": allow_origin,
                "allow_credentials": allow_creds
            }
    except Exception as e:
        log_result("4. CORS Preflight Check (OPTIONS)", False, str(e))
        return None

def test_unauthorized_auth_guard():
    start_time = time.time()
    try:
        # Request protected API endpoint without Bearer token
        url = f"{BACKEND_STAGING_URL}/api/assessments"
        req = urllib.request.Request(url, headers={"User-Agent": "AIRS-Staging-Tester/1.0"})
        with urllib.request.urlopen(req) as resp:
            code = resp.getcode()
            log_result("5. Auth Guard & 401 Handling", False, f"Unexpected 200 OK on protected endpoint: {code}")
            return None
    except urllib.error.HTTPError as e:
        code = e.code
        body_text = e.read().decode('utf-8')
        success = (code == 401)
        log_result("5. Auth Guard & 401 Handling", success,
                   f"Received expected HTTP 401 Unauthorized. Status={code}, Detail: {body_text.strip()}")
        return {
            "status": code,
            "response": body_text
        }
    except Exception as e:
        log_result("5. Auth Guard & 401 Handling", False, str(e))
        return None

def test_system_health():
    start_time = time.time()
    try:
        url = f"{BACKEND_STAGING_URL}/health/system"
        req = urllib.request.Request(url, headers={"User-Agent": "AIRS-Staging-Tester/1.0"})
        with urllib.request.urlopen(req) as resp:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            code = resp.getcode()
            body_json = json.loads(resp.read().decode('utf-8'))
            
            env = body_json.get("environment")
            success = (code == 200) and (env == "staging")
            log_result("6. System Status Endpoint (/health/system)", success,
                       f"Status={code}, Latency={latency_ms}ms, Env={env}, DemoMode={body_json.get('demo_mode')}, IsReadOnly={body_json.get('is_read_only')}")
            return {
                "status": code,
                "latency_ms": latency_ms,
                "body": body_json
            }
    except Exception as e:
        log_result("6. System Status Endpoint (/health/system)", False, str(e))
        return None

def run_all_tests():
    print("=================================================================")
    print("Starting Live Staging E2E Integration Validation Suite")
    print(f"Frontend URL: {FRONTEND_STAGING_URL}")
    print(f"Backend URL:  {BACKEND_STAGING_URL}")
    print("=================================================================\n")
    
    t1 = test_frontend_access()
    t2 = test_backend_health()
    t3 = test_backend_config()
    t4 = test_cors_preflight()
    t5 = test_unauthorized_auth_guard()
    t6 = test_system_health()
    
    print("\n=================================================================")
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    print(f"Validation Summary: {passed}/{total} tests passed ({round(passed/total*100, 1)}%)")
    print("=================================================================")
    
    return {
        "frontend": t1,
        "backend_health": t2,
        "backend_config": t3,
        "cors": t4,
        "auth_guard": t5,
        "system_health": t6,
        "passed": passed,
        "total": total
    }

if __name__ == "__main__":
    run_all_tests()
