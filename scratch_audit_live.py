"""Infrastructure Recovery Sprint — Live Deployment Audit Script.
Fetches HTML and JS bundles from all known Firebase Hosting sites
and extracts embedded environment variables, Firebase config, and API URLs.
READ-ONLY. Does not modify anything.
"""
import urllib.request
import re
import json
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Disable SSL verification for speed (not security-critical here)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SITES = [
    ("airs-staging-0384513977.web.app", "STAGING (primary)"),
    ("resilai-staging.web.app", "STAGING (resilai-staging)"),
    ("gen-lang-client-0384513977.web.app", "DEMO"),
    ("resilai-marketing.web.app", "MARKETING/PRODUCTION"),
    ("resilai-demo.web.app", "DEMO (resilai-demo)"),
    ("resilai-sentinel.web.app", "SENTINEL"),
]

BACKENDS = [
    ("https://airs-api-staging-227825933697.us-central1.run.app/health", "Staging Backend (new URL)"),
    ("https://airs-api-227825933697.us-central1.run.app/health", "Production Backend"),
    ("https://api.resilai.org/health", "Production Backend (custom domain)"),
    ("https://api-staging.resilai.org/health", "Staging Backend (custom domain)"),
]

def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace") if e.fp else ""
    except Exception as e:
        return 0, str(e)

def extract_scripts(html):
    return re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)

def extract_title(html):
    m = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
    return m.group(1) if m else "(no title)"

def search_in_js(js_text, patterns):
    results = {}
    for name, pat in patterns:
        matches = re.findall(pat, js_text)
        if matches:
            results[name] = list(set(matches))
    return results

print("=" * 80)
print("LIVE DEPLOYMENT AUDIT — INFRASTRUCTURE RECOVERY SPRINT")
print("=" * 80)

# 1. Backend health checks
print("\n" + "=" * 80)
print("SECTION 1: BACKEND HEALTH CHECKS")
print("=" * 80)
for url, label in BACKENDS:
    status, body = fetch(url)
    print(f"\n[{label}]")
    print(f"  URL: {url}")
    print(f"  Status: {status}")
    print(f"  Body: {body[:300]}")

# 2. Frontend site audits
JS_PATTERNS = [
    ("API_URL (airs-api)", r'(https?://airs-api[^\s"\'`,}]+)'),
    ("API_URL (api.resilai)", r'(https?://api[\.\-]?[^\s"\'`,}]*resilai[^\s"\'`,}]*)'),
    ("Firebase apiKey", r'apiKey\s*:\s*["\']([^"\']+)["\']'),
    ("Firebase authDomain", r'authDomain\s*:\s*["\']([^"\']+)["\']'),
    ("Firebase projectId", r'projectId\s*:\s*["\']([^"\']+)["\']'),
    ("VITE_APP_ENV", r'VITE_APP_ENV\s*[=:]\s*["\']?([a-z]+)'),
]

print("\n" + "=" * 80)
print("SECTION 2: FRONTEND SITE AUDITS")
print("=" * 80)

for host, label in SITES:
    url = f"https://{host}/"
    print(f"\n{'─' * 70}")
    print(f"[{label}] {url}")
    print(f"{'─' * 70}")

    status, html = fetch(url)
    print(f"  HTTP Status: {status}")
    print(f"  Title: {extract_title(html)}")

    if status == 0:
        print(f"  ERROR: {html[:200]}")
        continue

    scripts = extract_scripts(html)
    print(f"  Scripts found: {len(scripts)}")
    for s in scripts:
        print(f"    - {s}")

    # Fetch each JS bundle and search for embedded config
    main_bundle_found = False
    for script_src in scripts:
        if script_src.startswith("/"):
            js_url = f"https://{host}{script_src}"
        elif script_src.startswith("http"):
            js_url = script_src
        else:
            js_url = f"https://{host}/{script_src}"

        # Only fetch main index bundles and vendor bundles
        if "index" not in script_src and "vendor" not in script_src:
            continue

        js_status, js_body = fetch(js_url, timeout=15)
        if js_status != 200:
            print(f"  [JS FETCH FAILED] {script_src} -> {js_status}")
            continue

        findings = search_in_js(js_body, JS_PATTERNS)
        if findings:
            main_bundle_found = True
            print(f"\n  📦 Bundle: {script_src}")
            for key, vals in findings.items():
                for v in vals:
                    print(f"    {key}: {v}")

    if not main_bundle_found and scripts:
        print("  ⚠️  No embedded config found in any JS bundle")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
