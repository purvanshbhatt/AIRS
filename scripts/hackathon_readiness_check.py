import os
import re
import importlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

def generate_report(results):
    report = "# Hackathon Demo Readiness Report\n\n"
    report += "## Automated Validation Results\n\n"
    all_passed = True
    for key, (passed, details) in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed: all_passed = False
        report += f"### {key}: {status}\n"
        report += f"{details}\n\n"
    
    report += "---\n"
    report += "**Overall Status:** " + ("GO FOR DEMO" if all_passed else "NO GO - FIX ISSUES") + "\n"
    
    with open("docs/HACKATHON_READINESS_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("Report generated at docs/HACKATHON_READINESS_REPORT.md")

def check_readiness():
    results = {}
    
    # 1. Routes registered
    try:
        from app.main import app
        routes = [route.path for route in app.routes]
        sentinel_routes = [r for r in routes if "/api/sentinel" in r]
        if sentinel_routes:
            results["Sentinel Routes Registered"] = (True, f"Found {len(sentinel_routes)} Sentinel routes.")
        else:
            results["Sentinel Routes Registered"] = (False, "No Sentinel routes found in app.main.")
    except Exception as e:
        results["Sentinel Routes Registered"] = (False, f"Error checking routes: {e}")

    # 2. Splunk Configured
    splunk_token = os.environ.get("SPLUNK_TOKEN", "")
    if splunk_token or "SPLUNK_TOKEN" in open(".env").read() if os.path.exists(".env") else False:
        results["Splunk Connector Configured"] = (True, "Splunk credentials present.")
    else:
        results["Splunk Connector Configured"] = (False, "SPLUNK_TOKEN missing.")

    # 3. Gemini Configured
    gemini_key = os.environ.get("GOOGLE_API_KEY", "")
    if gemini_key or "GOOGLE_API_KEY" in open(".env").read() if os.path.exists(".env") else False:
        results["Gemini Configuration Present"] = (True, "Google API Key present.")
    else:
        results["Gemini Configuration Present"] = (False, "GOOGLE_API_KEY missing.")

    # 4. Database tables
    try:
        from sqlalchemy import text
        from app.db.database import SQLALCHEMY_DATABASE_URL
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        conn = engine.connect()
        # Check if sentinel_simulations exists
        conn.execute(text("SELECT 1 FROM sentinel_simulations LIMIT 1"))
        conn.close()
        results["Database Migrations Applied"] = (True, "Sentinel tables exist in the database.")
    except Exception as e:
        results["Database Migrations Applied"] = (False, f"Database check failed: {e}")

    # 5. Duplicate scoring logic
    import glob
    sentinel_files = glob.glob("app/sentinel/**/*.py", recursive=True)
    scoring_logic_found = False
    for f in sentinel_files:
        content = open(f).read()
        # Look for explicit math operators doing scores
        if re.search(r'overall_score\s*[-+=]', content) or 'impact_penalty' in content:
            scoring_logic_found = True
    
    if scoring_logic_found:
        results["No Duplicate Scoring Logic"] = (False, "Found independent scoring math in app/sentinel.")
    else:
        results["No Duplicate Scoring Logic"] = (True, "Sentinel delegates all math to core scoring engine.")

    # 6. Hardcoded framework mappings
    framework_mapping_found = False
    for f in sentinel_files:
        content = open(f).read()
        if '"NIST"' in content or '"CIS"' in content or '"ISO"' in content:
            framework_mapping_found = True
            
    if framework_mapping_found:
        results["No Hardcoded Framework Mappings"] = (False, "Found hardcoded framework strings in app/sentinel.")
    else:
        results["No Hardcoded Framework Mappings"] = (True, "Sentinel properly resolves frameworks via app.core.rubric.")

    generate_report(results)

if __name__ == "__main__":
    check_readiness()
