#!/usr/bin/env python3
"""Quick test: Visual date picker interaction"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright
import subprocess
import json

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")

def get_credentials():
    result = subprocess.run(
        ["op", "item", "get", "sellerboard", "--fields", "label=username,label=password", "--format", "json"],
        capture_output=True, text=True, check=True
    )
    creds = json.loads(result.stdout)
    username = next(c["value"] for c in creds if c["label"] == "username")
    password = next(c["value"] for c in creds if c["label"] == "password")
    return username, password

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    
    # Login
    username, password = get_credentials()
    page.goto("https://app.sellerboard.com/en/export")
    page.wait_for_selector('input[placeholder*="mail" i]', timeout=15000)
    page.locator('input[placeholder*="mail" i]').first.fill(username)
    page.locator('input[type="password"]').first.fill(password)
    page.locator('button:has-text("Continue")').first.click()
    page.wait_for_load_state("networkidle", timeout=30000)
    
    print("✅ Logged in")
    
    # Navigate to Dashboard by product
    page.goto("https://app.sellerboard.com/en/export")
    time.sleep(2)
    page.evaluate('document.querySelectorAll(".modal-backdrop, [class*=\\"backdrop\\"]").forEach(el => el.remove())')
    
    # Click Dashboard by product
    page.evaluate('''
        () => {
            const el = document.querySelector('[ng-click*="DashboardGoods"]');
            if (el && window.angular) {
                const scope = angular.element(el).scope();
                scope.$apply(() => scope.setCurrentType('DashboardGoods'));
            }
        }
    ''')
    time.sleep(3)
    print("✅ Navigated to export page")
    
    # TEST: Set date range using VISUAL picker
    print("📅 Testing visual date picker...")
    
    # Clear existing dates and click "From" field
    from_input = page.locator('textbox').filter(has_text="02/02/2026").first
    from_input.click()
    time.sleep(1)
    
    # The calendar should now be open
    # Click "previous month" arrow several times to go back 3 months (Nov 2025)
    for i in range(3):
        page.locator('table columnheader').filter(has=page.locator('img')).first.click()
        time.sleep(0.5)
    
    # Click day "4" for Nov 4
    page.locator('table cell:has-text("4")').first.click()
    time.sleep(1)
    
    print("✅ From date set to Nov 4")
    
    # Screenshot to verify
    page.screenshot(path=str(DATA_DIR / "screenshots/test_dates_set.png"))
    
    # Check what the date inputs show now
    from_value = page.locator('textbox').first.input_value()
    print(f"From date value: {from_value}")
    
    # Keep browser open for inspection
    print("\n🔍 Inspect the page - press Enter to close browser...")
    input()
    
    browser.close()
