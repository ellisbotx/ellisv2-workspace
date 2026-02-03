#!/usr/bin/env python3
"""
Capture the actual form submission data for Sellerboard export.
This will help us understand what data is being sent when Download is clicked.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from sellerboard_auto_export import get_credentials, login, switch_brand, close_popups, take_screenshot, REPORTS_URL

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")

def main():
    print("Sellerboard Form Capture Tool")
    print("="*60)
    
    username, password = get_credentials()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        # Capture all network requests
        requests_log = []
        
        def log_request(request):
            if 'export' in request.url.lower() or 'download' in request.url.lower():
                requests_log.append({
                    'url': request.url,
                    'method': request.method,
                    'post_data': request.post_data,
                    'headers': dict(request.headers),
                })
                print(f"\n🌐 CAPTURED REQUEST:")
                print(f"   URL: {request.url}")
                print(f"   Method: {request.method}")
                if request.post_data:
                    print(f"   POST Data: {request.post_data}")
        
        page.on('request', log_request)
        
        try:
            # Login and navigate
            login(page, username, password)
            switch_brand(page, "Kinfolk")
            
            # Navigate to export page
            print("\nNavigating to export page...")
            page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            close_popups(page, aggressive=True)
            time.sleep(1)
            
            # Click Dashboard by product
            print("Clicking Dashboard by product...")
            page.evaluate('''
                () => {
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    const element = document.querySelector('[ng-click*="DashboardGoods"]');
                    if (element) element.click();
                }
            ''')
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)
            close_popups(page, aggressive=True)
            
            # Get form details
            print("\n📋 FORM DETAILS:")
            form_info = page.evaluate('''
                () => {
                    const form = document.querySelector('form');
                    if (!form) return {found: false};
                    
                    const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
                    const inputData = inputs.map(inp => ({
                        name: inp.name || inp.id,
                        type: inp.type,
                        value: inp.value,
                        tagName: inp.tagName
                    }));
                    
                    return {
                        found: true,
                        action: form.action,
                        method: form.method,
                        id: form.id,
                        inputs: inputData
                    };
                }
            ''')
            
            if form_info['found']:
                print(f"   Action: {form_info['action']}")
                print(f"   Method: {form_info['method']}")
                print(f"   Inputs:")
                for inp in form_info['inputs']:
                    if inp['name']:
                        print(f"      {inp['name']} ({inp['type']}): {inp['value']}")
            
            # Click download and monitor
            print("\n🖱️  Clicking Download button...")
            print("   (Network requests will be captured)")
            
            page.evaluate('''
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const downloadBtn = buttons.find(btn => btn.textContent?.trim() === 'Download');
                    if (downloadBtn) downloadBtn.click();
                }
            ''')
            
            # Wait for any async requests
            print("   Waiting 10 seconds for requests...")
            time.sleep(10)
            
            # Print captured requests
            print("\n📊 CAPTURED EXPORT REQUESTS:")
            if requests_log:
                for req in requests_log:
                    print(f"\n   URL: {req['url']}")
                    print(f"   Method: {req['method']}")
                    if req['post_data']:
                        print(f"   POST Data: {req['post_data']}")
            else:
                print("   (No export-related requests captured)")
            
            print("\n✅ Capture complete! Browser will close in 10 seconds...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
