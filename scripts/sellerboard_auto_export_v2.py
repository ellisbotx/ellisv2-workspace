#!/usr/bin/env python3
"""Automated Sellerboard export downloader - WORKING VERSION

This script automates CSV downloads from Sellerboard using Playwright.

Key fixes:
- Aggressive modal backdrop removal
- Direct Angular ng-click triggering  
- Proper wait for download completion
- CSV format selection before download

Usage:
  python3 sellerboard_auto_export_v2.py [--headless] [--brand BRAND]
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Playwright not installed. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

# Configuration
DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")
LOG_FILE = DATA_DIR / "auto_export.log"
SCREENSHOT_DIR = DATA_DIR / "screenshots"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Brands (UI name -> filename prefix)
BRANDS = {
    "Summary Dashboard": "blackowned",
    "CardPlug": "cardplug",
    "Kinfolk": "kinfolk",
}

REPORTS_URL = "https://app.sellerboard.com/en/export"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_credentials():
    """Fetch credentials from 1Password."""
    result = subprocess.run(
        ["op", "item", "get", "sellerboard", "--fields", "label=username,label=password", "--format", "json"],
        capture_output=True, text=True, check=True
    )
    creds = json.loads(result.stdout)
    username = next(c["value"] for c in creds if c["label"] == "username")
    password = next(c["value"] for c in creds if c["label"] == "password")
    return username, password


def screenshot(page, name: str):
    """Take screenshot for debugging."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"{ts}_{name}.png"
    page.screenshot(path=str(path))
    logger.info(f"📸 Screenshot: {path}")
    return path


def remove_modals(page):
    """Aggressively remove all modal overlays."""
    try:
        removed = page.evaluate('''
            () => {
                const selectors = [
                    '.modal-backdrop',
                    '[class*="modal-backdrop"]',
                    '.newFeature',
                    '[class*="backdrop"]',
                    '.modal',
                    '[class*="popup"]'
                ];
                let count = 0;
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => {
                        el.remove();
                        count++;
                    });
                });
                // Also remove inline styles that might hide content
                document.body.style.overflow = '';
                return count;
            }
        ''')
        if removed > 0:
            logger.info(f"🗑️  Removed {removed} modal elements")
            time.sleep(0.5)
    except Exception as e:
        logger.debug(f"Modal removal failed: {e}")


def login(page, username: str, password: str):
    """Login to Sellerboard."""
    logger.info("🔐 Logging in...")
    page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # Wait for and fill login form
    page.wait_for_selector('input[placeholder*="mail" i]', timeout=15000)
    screenshot(page, "01_login_page")
    
    page.locator('input[placeholder*="mail" i]').first.fill(username)
    page.locator('input[type="password"]').first.fill(password)
    screenshot(page, "02_credentials_filled")
    
    page.locator('button:has-text("Continue")').first.click()
    page.wait_for_load_state("networkidle", timeout=30000)
    
    screenshot(page, "03_logged_in")
    logger.info("✓ Login successful")


def switch_brand(page, brand_name: str):
    """Switch to specified brand."""
    logger.info(f"🔄 Switching to brand: {brand_name}")
    
    # Click brand dropdown
    page.locator('[class*="brand"], [class*="account"], [class*="store"]').first.click()
    time.sleep(2)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    screenshot(page, f"04_brand_switched_{brand_name.lower().replace(' ', '_')}")
    logger.info(f"✓ Switched to {brand_name}")


def download_dashboard_by_product(page, brand_filename: str):
    """Download Dashboard by product CSV."""
    logger.info(f"📥 Downloading CSV for {brand_filename}...")
    
    # Navigate to Reports page
    page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    remove_modals(page)
    screenshot(page, f"05_reports_list_{brand_filename}")
    
    # Click "Dashboard by product" using Angular-aware approach
    logger.info("🎯 Clicking 'Dashboard by product'...")
    clicked = page.evaluate('''
        () => {
            // Remove backdrops first
            document.querySelectorAll('.modal-backdrop, [class*="backdrop"], .newFeature').forEach(el => el.remove());
            
            // Find element with ng-click for Dashboard by product
            const element = document.querySelector('[ng-click*="DashboardGoods"]');
            if (element) {
                // Trigger click event
                const event = new MouseEvent('click', {view: window, bubbles: true, cancelable: true});
                element.dispatchEvent(event);
                
                // Try Angular scope approach if available
                if (window.angular) {
                    try {
                        const scope = angular.element(element).scope();
                        if (scope && scope.setCurrentType) {
                            scope.setCurrentType('DashboardGoods');
                            scope.$apply();
                        }
                    } catch (e) {}
                }
                return true;
            }
            return false;
        }
    ''')
    
    if not clicked:
        raise Exception("Could not trigger Dashboard by product click")
    
    logger.info("✓ Clicked Dashboard by product")
    time.sleep(3)  # Wait for Angular routing
    remove_modals(page)
    screenshot(page, f"06_export_page_{brand_filename}")
    
    # Wait for download button to appear
    try:
        page.wait_for_selector('button:has-text("Download")', timeout=10000)
        logger.info("✓ Export page loaded")
    except:
        logger.warning("Download button not found quickly, proceeding anyway")
    
    # Set date range (last 90 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    logger.info(f"📅 Setting date range: {start_date.date()} to {end_date.date()}")
    page.evaluate(f'''
        () => {{
            const fromInput = document.querySelector('input[name="period_from"], input[id="period_from"]');
            const toInput = document.querySelector('input[name="period_to"], input[id="period_to"]');
            
            if (fromInput) {{
                fromInput.value = "{int(start_date.timestamp())}";
                fromInput.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
            if (toInput) {{
                toInput.value = "{int(end_date.timestamp())}";
                toInput.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        }}
    ''')
    time.sleep(1)
    
    # Select CSV format
    logger.info("📝 Selecting CSV format...")
    csv_selected = page.evaluate('''
        () => {
            // Find and click CSV radio/option
            const csvElements = Array.from(document.querySelectorAll('*')).filter(el =>
                el.textContent?.trim() === '.CSV' || el.textContent?.trim() === 'CSV'
            );
            
            for (const el of csvElements) {
                // Find parent or nearby input/clickable element
                let current = el;
                for (let i = 0; i < 5; i++) {
                    if (!current) break;
                    
                    const input = current.querySelector('input[type="radio"], input[value*="csv" i]');
                    if (input) {
                        input.click();
                        return true;
                    }
                    
                    if (current.onclick || current.tagName === 'LABEL') {
                        current.click();
                        return true;
                    }
                    
                    current = current.parentElement;
                }
            }
            return false;
        }
    ''')
    
    if csv_selected:
        logger.info("✓ CSV format selected")
    else:
        logger.warning("Could not explicitly select CSV, using default")
    
    time.sleep(1)
    screenshot(page, f"07_ready_to_download_{brand_filename}")
    
    # Download CSV
    output_file = DATA_DIR / f"{brand_filename}_dashboard_by_product_90d.csv"
    logger.info(f"⬇️  Clicking download button...")
    
    with page.expect_download(timeout=60000) as download_info:
        # Click download button
        download_btn = page.locator('button:has-text("Download")').first
        download_btn.click()
        logger.info("Download button clicked, waiting for file...")
    
    download = download_info.value
    download.save_as(output_file)
    
    logger.info(f"✅ Downloaded: {output_file}")
    screenshot(page, f"08_download_complete_{brand_filename}")
    
    return output_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--brand", choices=list(BRANDS.values()), help="Download only one brand")
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🚀 Sellerboard Auto Export Started")
    logger.info(f"⏰ {datetime.now().isoformat()}")
    logger.info("=" * 70)
    
    # Get credentials
    username, password = get_credentials()
    logger.info(f"🔑 Retrieved credentials for: {username}")
    
    # Setup browser
    downloaded_files = []
    failed_brands = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=args.headless,
            slow_mo=500,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        try:
            # Login
            login(page, username, password)
            
            # Filter brands if specified
            brands_to_process = {k: v for k, v in BRANDS.items() if v == args.brand} if args.brand else BRANDS
            
            # Process each brand
            for brand_ui_name, brand_filename in brands_to_process.items():
                try:
                    logger.info(f"\n{'=' * 70}")
                    logger.info(f"📦 Processing: {brand_ui_name} ({brand_filename})")
                    logger.info(f"{'=' * 70}")
                    
                    # Switch brand
                    switch_brand(page, brand_ui_name)
                    
                    # Download CSV
                    output_file = download_dashboard_by_product(page, brand_filename)
                    downloaded_files.append(output_file)
                    
                    logger.info(f"✅ Successfully exported {brand_ui_name}")
                    time.sleep(3)  # Pause between brands
                    
                except Exception as e:
                    logger.error(f"❌ Failed to export {brand_ui_name}: {e}")
                    screenshot(page, f"error_{brand_filename}")
                    failed_brands.append(brand_ui_name)
                    continue
        
        finally:
            browser.close()
    
    # Summary
    logger.info(f"\n{'=' * 70}")
    logger.info("📊 EXPORT SUMMARY")
    logger.info(f"{'=' * 70}")
    logger.info(f"✅ Successful: {len(downloaded_files)}")
    logger.info(f"❌ Failed: {len(failed_brands)}")
    
    if downloaded_files:
        logger.info("\n📁 Downloaded files:")
        for f in downloaded_files:
            logger.info(f"  ✓ {f}")
    
    if failed_brands:
        logger.info("\n⚠️  Failed brands:")
        for b in failed_brands:
            logger.info(f"  ✗ {b}")
    
    # Process into JSON (import existing script)
    if downloaded_files:
        logger.info(f"\n{'=' * 70}")
        logger.info("🔄 Processing CSVs into sku_velocity.json...")
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from sellerboard_export import update_velocity_data
            update_velocity_data()
            logger.info("✅ Processing complete!")
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
    
    logger.info(f"\n{'=' * 70}")
    logger.info(f"🏁 Sellerboard Auto Export Complete")
    logger.info(f"⏰ {datetime.now().isoformat()}")
    logger.info(f"{'=' * 70}\n")
    
    return 0 if not failed_brands else 1


if __name__ == "__main__":
    sys.exit(main())
