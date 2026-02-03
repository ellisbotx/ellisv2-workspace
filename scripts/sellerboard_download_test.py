#!/usr/bin/env python3
"""
Quick test script to debug the download button on Sellerboard.
This will navigate to the page and print out what buttons/forms exist.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from sellerboard_auto_export import get_credentials, login, switch_brand, close_popups, take_screenshot

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")
SCREENSHOT_DIR = DATA_DIR / "screenshots"
REPORTS_URL = "https://app.sellerboard.com/en/export"

def debug_download_page(page):
    """Debug what's on the download page."""
    print("\n" + "="*60)
    print("DEBUGGING DOWNLOAD PAGE")
    print("="*60)
    
    # Get page URL
    print(f"Current URL: {page.url}")
    
    # Find all buttons
    print("\n--- ALL BUTTONS ---")
    buttons = page.evaluate('''
        () => {
            const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"], a.btn'));
            return buttons.map((btn, idx) => ({
                index: idx,
                tag: btn.tagName,
                type: btn.type || '',
                text: btn.textContent?.trim().substring(0, 50) || '',
                value: btn.value || '',
                id: btn.id || '',
                class: btn.className || '',
                onclick: btn.onclick ? 'has onclick' : '',
                ngClick: btn.getAttribute('ng-click') || ''
            }));
        }
    ''')
    for btn in buttons:
        if btn['text'] or btn['value']:
            print(f"  [{btn['index']}] {btn['tag']} - Text: '{btn['text']}' Value: '{btn['value']}'")
            if btn['ngClick']:
                print(f"       ng-click: {btn['ngClick']}")
    
    # Find all forms
    print("\n--- ALL FORMS ---")
    forms = page.evaluate('''
        () => {
            const forms = Array.from(document.querySelectorAll('form'));
            return forms.map((form, idx) => ({
                index: idx,
                action: form.action || '',
                method: form.method || '',
                id: form.id || '',
                class: form.className || ''
            }));
        }
    ''')
    for form in forms:
        print(f"  [{form['index']}] Action: {form['action']} Method: {form['method']}")
    
    # Check for download-related elements
    print("\n--- DOWNLOAD-RELATED ELEMENTS ---")
    download_elements = page.evaluate('''
        () => {
            const allElements = Array.from(document.querySelectorAll('*'));
            const downloadElements = allElements.filter(el => {
                const text = (el.textContent || '').toLowerCase();
                const value = (el.value || '').toLowerCase();
                return text.includes('download') || text.includes('export') || 
                       value.includes('download') || value.includes('export');
            });
            return downloadElements.slice(0, 10).map((el, idx) => ({
                index: idx,
                tag: el.tagName,
                text: el.textContent?.trim().substring(0, 50) || '',
                value: el.value || '',
                onclick: el.onclick ? 'has onclick' : '',
                ngClick: el.getAttribute('ng-click') || ''
            }));
        }
    ''')
    for el in download_elements:
        print(f"  [{el['index']}] {el['tag']} - '{el['text']}' / '{el['value']}'")
        if el['ngClick']:
            print(f"       ng-click: {el['ngClick']}")
    
    print("\n" + "="*60)

def main():
    print("Sellerboard Download Debug Tool")
    print("="*60)
    
    # Get credentials
    username, password = get_credentials()
    print(f"Using account: {username}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        page = context.new_page()
        
        try:
            # Login
            login(page, username, password)
            
            # Switch to Kinfolk
            switch_brand(page, "Kinfolk")
            
            # Navigate to Reports
            print("\nNavigating to Reports page...")
            page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Close popups
            close_popups(page, aggressive=True)
            time.sleep(1)
            
            take_screenshot(page, "debug_01_reports_page")
            
            # Click Dashboard by product
            print("\nClicking Dashboard by product...")
            page.evaluate('''
                () => {
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    const element = document.querySelector('[ng-click*="DashboardGoods"]');
                    if (element) {
                        element.click();
                    }
                }
            ''')
            
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)
            
            close_popups(page, aggressive=True)
            time.sleep(1)
            
            take_screenshot(page, "debug_02_dashboard_by_product")
            
            # Debug the page
            debug_download_page(page)
            
            # Keep browser open for manual inspection
            print("\n🔍 Browser will stay open for 60 seconds for manual inspection...")
            print("Check the page and look for the download button!")
            time.sleep(60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            take_screenshot(page, "debug_error")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
