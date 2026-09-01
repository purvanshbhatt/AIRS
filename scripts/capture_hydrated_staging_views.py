"""
Capture fully hydrated staging UI views with demo data loaded.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"C:\Users\purva\.gemini\antigravity\brain\7d36cbd5-e19e-470b-87c3-467f8b5828ba"

def capture_hydrated():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.5
        )
        page = context.new_page()
        
        # Go to Landing and click Explore Demo / Enter Demo
        page.goto("http://127.0.0.1:5173/", wait_until="networkidle")
        time.sleep(1)
        
        # Click "Enter Demo" or "Explore Demo"
        enter_demo_btn = page.locator("button:has-text('Enter Demo'), button:has-text('Explore Demo')").first
        if enter_demo_btn.is_visible():
            enter_demo_btn.click()
            time.sleep(2)
        else:
            page.goto("http://127.0.0.1:5173/morning-brief")
            time.sleep(2)
            
        # 1. Morning Brief
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_morning_brief.png"))
        print("Captured hydrated morning brief.")
        
        # 2. Needs Attention
        page.goto("http://127.0.0.1:5173/needs-attention", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_needs_attention.png"))
        print("Captured hydrated needs attention.")
        
        # 3. Recovery
        page.goto("http://127.0.0.1:5173/recovery", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_recovery.png"))
        print("Captured hydrated recovery.")
        
        # 4. Connectors
        page.goto("http://127.0.0.1:5173/connectors", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_connectors.png"))
        print("Captured hydrated connectors.")
        
        # 5. Documents
        page.goto("http://127.0.0.1:5173/documents", wait_until="networkidle")
        time.sleep(1)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_documents.png"))
        print("Captured hydrated documents.")
        
        # 6. Governance
        page.goto("http://127.0.0.1:5173/governance", wait_until="networkidle")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_governance.png"))
        print("Captured hydrated governance.")
        
        # 7. Identity Domain
        page.goto("http://127.0.0.1:5173/identity", wait_until="networkidle")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_domain_identity.png"))
        print("Captured hydrated identity.")
        
        # 8. Backups Domain
        page.goto("http://127.0.0.1:5173/backups", wait_until="networkidle")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "live_staging_domain_backups.png"))
        print("Captured hydrated backups.")
        
        context.close()
        browser.close()
        print("Done capturing hydrated views.")

if __name__ == "__main__":
    capture_hydrated()
