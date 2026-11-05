"""
Capture full screenshot suite for ResilAI Product Integrity & Staging Validation.
Saves screenshots to artifact directory.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\purva\.gemini\antigravity\brain\7d36cbd5-e19e-470b-87c3-467f8b5828ba"

def capture_all_views():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Desktop context
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.5
        )
        page = context.new_page()
        
        # 1. Landing Page
        print("Capturing Landing page...")
        page.goto("http://localhost:5173/", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_landing.png"))
        
        # 2. Login Page
        print("Capturing Login page...")
        page.goto("http://localhost:5173/login", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_login.png"))
        
        # 3. Enter Sandbox / Morning Brief
        print("Capturing Morning Brief (Today) page...")
        page.goto("http://localhost:5173/morning-brief", wait_until="networkidle")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_morning_brief.png"))
        
        # 4. Needs Attention
        print("Capturing Needs Attention page...")
        page.goto("http://localhost:5173/needs-attention", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_needs_attention.png"))
        
        # 5. Recovery
        print("Capturing Recovery Readiness page...")
        page.goto("http://localhost:5173/recovery", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_recovery.png"))
        
        # 6. Connectors
        print("Capturing Connectors page...")
        page.goto("http://localhost:5173/connectors", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_connectors.png"))
        
        # 7. Documents
        print("Capturing Documents page...")
        page.goto("http://localhost:5173/documents", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_documents.png"))
        
        # 8. Governance
        print("Capturing Governance page...")
        page.goto("http://localhost:5173/governance", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_governance.png"))
        
        # 9. Domain Identity
        print("Capturing Identity Domain page...")
        page.goto("http://localhost:5173/operations/identity", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_domain_identity.png"))
        
        # 10. Domain Backups
        print("Capturing Backups Domain page...")
        page.goto("http://localhost:5173/operations/backups", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_domain_backups.png"))
        
        # 11. Methodology
        print("Capturing Scoring Methodology page...")
        page.goto("http://localhost:5173/docs/methodology", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_methodology.png"))
        
        # 12. Frameworks
        print("Capturing Framework Mappings page...")
        page.goto("http://localhost:5173/docs/frameworks", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_frameworks.png"))
        
        context.close()
        
        # Mobile context
        print("Capturing Mobile view...")
        mobile_context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            device_scale_factor=2
        )
        mobile_page = mobile_context.new_page()
        mobile_page.goto("http://localhost:5173/morning-brief", wait_until="networkidle")
        time.sleep(1.5)
        mobile_page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_mobile.png"))
        mobile_context.close()
        
        browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    capture_all_views()
