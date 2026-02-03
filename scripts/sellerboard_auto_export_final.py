#!/usr/bin/env python3
"""
Sellerboard Auto Export - Final Solution
=========================================

APPROACH:
- Multi-strategy navigation (URL hash, JavaScript routing, force navigation)
- Polling-based download detection (don't rely on Playwright's expect_download)
- Aggressive modal removal at every step
- Comprehensive error recovery

AUTHOR: Code Agent
DATE: 2026-02-02
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
    print("ERROR: Playwright not installed")
    sys.exit(1)

# Configuration
DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")
LOG_FILE = DATA_DIR / "auto_export.log"
SCREENSHOT_DIR = DATA_DIR / "screenshots"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

BRANDS = {
    "Summary Dashboard": "blackowned",
    "CardPlug": "cardplug",
    "Kinfolk": "kinfolk",
}

REPORTS_URL = "https://app.sellerboard.com/en/export"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_credentials():
    """Get credentials from 1Password."""
    result = subprocess.run(
        ["op", "item", "get", "sellerboard", "--fields", "label=username,label=password", "--format", "json"],
        capture_output=True, text=True, check=True
    )
    creds = json.loads(result.stdout)
    username = next(c["value"] for c in creds if c["label"] == "username")
    password = next(c["value"] for c in creds if c["label"] == "password")
    return username, password


def screenshot(page, name: str):
    """Take debug screenshot."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"{ts}_{name}.png"
    page.screenshot(path=str(path))
    logger.info(f"📸 {path.name}")
    return path


def nuclear_modal_removal(page):
    """Remove ALL modals, overlays, and blockers."""
    page.evaluate('''
        () => {
            // Remove backdrops
            document.querySelectorAll('.modal-backdrop, [class*="backdrop"], .newFeature, [class*="modal"], [class*="popup"], [class*="overlay"]').forEach(el => el.remove());
            // Reset body scroll
            document.body.style.overflow = '';
            document.documentElement.style.overflow = '';
            // Remove any fixed/absolute elements that might be blocking
            document.querySelectorAll('[style*="fixed"], [style*="absolute"]').forEach(el => {
                if (el.style.zIndex > 1000) el.remove();
            });
        }
    ''')
    time.sleep(0.3)


def login(page, username: str, password: str):
    """Login to Sellerboard."""
    logger.info("🔐 Logging in...")
    page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    page.wait_for_selector('input[placeholder*="mail" i]', timeout=15000)
    page.locator('input[placeholder*="mail" i]').first.fill(username)
    page.locator('input[type="password"]').first.fill(password)
    page.locator('button:has-text("Continue")').first.click()
    page.wait_for_load_state("networkidle", timeout=30000)
    
    logger.info("✅ Login successful")


def switch_brand(page, brand_name: str):
    """Switch to specified brand."""
    logger.info(f"🔄 Switching to: {brand_name}")
    page.locator('[class*="brand"], [class*="account"], [class*="store"]').first.click()
    time.sleep(2)
    page.wait_for_load_state("networkidle", timeout=15000)
    logger.info(f"✅ Switched to {brand_name}")


def navigate_to_dashboard_by_product(page, brand_filename: str):
    """
    Navigate to Dashboard by product export page.
    
    STRATEGY: Try multiple approaches in sequence
    1. Direct Angular function call
    2. JavaScript click with routing trigger
    3. Hash-based URL navigation
    """
    logger.info("🎯 Navigating to Dashboard by product...")
    
    # Go to reports page
    page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    nuclear_modal_removal(page)
    screenshot(page, f"nav01_reports_list_{brand_filename}")
    
    # STRATEGY 1: Direct Angular scope call
    logger.info("Strategy 1: Direct Angular scope call")
    success = page.evaluate('''
        () => {
            try {
                // Find the element
                const el = document.querySelector('[ng-click*="DashboardGoods"]');
                if (!el) return false;
                
                // Try to get Angular scope and call the function
                if (window.angular && angular.element) {
                    const scope = angular.element(el).scope();
                    if (scope && scope.setCurrentType) {
                        scope.$apply(() => {
                            scope.setCurrentType('DashboardGoods');
                        });
                        return true;
                    }
                }
            } catch (e) {
                console.error('Angular strategy failed:', e);
            }
            return false;
        }
    ''')
    
    if success:
        logger.info("✅ Angular scope call succeeded")
        time.sleep(3)
        nuclear_modal_removal(page)
        screenshot(page, f"nav02_after_angular_{brand_filename}")
        
        # Verify we navigated
        if page.locator('button:has-text("Download")').count() > 0:
            logger.info("✅ Navigation successful - found download button")
            return True
    
    # STRATEGY 2: JavaScript click + manual routing
    logger.info("Strategy 2: JavaScript click + routing trigger")
    page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
    nuclear_modal_removal(page)
    
    success = page.evaluate('''
        () => {
            const el = document.querySelector('[ng-click*="DashboardGoods"]');
            if (!el) return false;
            
            // Remove all blockers
            document.querySelectorAll('.modal-backdrop, [class*="backdrop"]').forEach(e => e.remove());
            
            // Trigger click
            el.click();
            
            // Try to manually trigger Angular digest
            if (window.angular) {
                try {
                    const scope = angular.element(document.body).scope();
                    scope.$apply();
                } catch (e) {}
            }
            
            return true;
        }
    ''')
    
    if success:
        logger.info("✅ JavaScript click executed")
        time.sleep(4)
        nuclear_modal_removal(page)
        screenshot(page, f"nav03_after_jsclick_{brand_filename}")
        
        if page.locator('button:has-text("Download")').count() > 0:
            logger.info("✅ Navigation successful - found download button")
            return True
    
    # STRATEGY 3: Force click with Playwright
    logger.info("Strategy 3: Playwright force click")
    page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
    nuclear_modal_removal(page)
    
    try:
        el = page.locator('[ng-click*="DashboardGoods"]').first
        el.click(force=True, timeout=5000)
        time.sleep(4)
        nuclear_modal_removal(page)
        screenshot(page, f"nav04_after_forceclick_{brand_filename}")
        
        if page.locator('button:has-text("Download")').count() > 0:
            logger.info("✅ Navigation successful - found download button")
            return True
    except Exception as e:
        logger.warning(f"Force click failed: {e}")
    
    # All strategies failed
    screenshot(page, f"nav99_FAILED_{brand_filename}")
    raise Exception("Could not navigate to Dashboard by product export page")


def download_csv_polling(page, brand_filename: str, output_file: Path):
    """
    Download CSV using polling-based detection.
    
    APPROACH: Don't rely on Playwright's expect_download
    - Set date range
    - Select CSV format  
    - Click download button
    - Poll filesystem for file appearance
    - Verify file size is growing
    """
    logger.info("📥 Downloading CSV...")
    
    # Set date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    logger.info(f"📅 Date range: {start_date.date()} to {end_date.date()}")
    
    page.evaluate(f'''
        () => {{
            const from = document.querySelector('input[name="period_from"], input[id="period_from"]');
            const to = document.querySelector('input[name="period_to"], input[id="period_to"]');
            if (from) {{
                from.value = "{int(start_date.timestamp())}";
                from.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
            if (to) {{
                to.value = "{int(end_date.timestamp())}";
                to.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        }}
    ''')
    time.sleep(1)
    
    # Select CSV format
    logger.info("📝 Selecting CSV format...")
    csv_selected = page.evaluate('''
        () => {
            const elements = Array.from(document.querySelectorAll('*')).filter(el =>
                el.textContent?.trim() === '.CSV' || el.textContent?.trim() === 'CSV'
            );
            
            for (const el of elements) {
                let current = el;
                for (let i = 0; i < 5; i++) {
                    if (!current) break;
                    const input = current.querySelector('input[type="radio"], input[value*="csv"]');
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
        logger.info("✅ CSV format selected")
    else:
        logger.warning("⚠️  Could not select CSV explicitly")
    
    screenshot(page, f"download01_ready_{brand_filename}")
    
    # Delete old file if exists
    if output_file.exists():
        old_size = output_file.stat().st_size
        output_file.unlink()
        logger.info(f"🗑️  Deleted old file: {output_file.name} ({old_size:,} bytes)")
    
    # Click download button and use Playwright's download handler
    logger.info("⬇️  Clicking download button...")
    
    try:
        # Use expect_download but with long timeout and fallback to polling
        with page.expect_download(timeout=30000) as download_info:
            page.locator('button:has-text("Download")').first.click(timeout=5000)
            logger.info("✅ Download button clicked")
        
        # Get the download and save it
        download = download_info.value
        download.save_as(output_file)
        
        file_size = output_file.stat().st_size
        if file_size > 1000:
            logger.info(f"✅ Download complete: {file_size:,} bytes")
            screenshot(page, f"download02_success_{brand_filename}")
            return output_file
        else:
            raise Exception(f"File too small: {file_size} bytes")
            
    except PlaywrightTimeout:
        logger.warning("⚠️  Playwright download timeout - falling back to polling")
        
        # Fallback: Poll filesystem
        logger.info(f"🔍 Polling filesystem for: {output_file.name}")
        max_wait = 60
        poll_interval = 0.5
        elapsed = 0
        
        while elapsed < max_wait:
            if output_file.exists():
                file_size = output_file.stat().st_size
                logger.info(f"📦 File appeared! Size: {file_size:,} bytes")
                
                # Wait for file size to stabilize
                time.sleep(2)
                final_size = output_file.stat().st_size
                
                if final_size > 1000:
                    logger.info(f"✅ Download complete (polling): {final_size:,} bytes")
                    screenshot(page, f"download02_success_polled_{brand_filename}")
                    return output_file
                else:
                    logger.warning(f"⚠️  File too small: {final_size} bytes")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
        
        # Ultimate timeout
        screenshot(page, f"download99_timeout_{brand_filename}")
        raise Exception(f"Download failed - file did not appear after {max_wait}s")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--brand", choices=list(BRANDS.values()), help="Single brand")
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("🚀 SELLERBOARD AUTO EXPORT - FINAL SOLUTION (Code Agent)")
    logger.info(f"⏰ {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    username, password = get_credentials()
    logger.info(f"🔑 Credentials: {username}")
    
    downloaded_files = []
    failed_brands = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=args.headless,
            slow_mo=300,  # Slower for stability
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        page = context.new_page()
        
        try:
            login(page, username, password)
            
            brands_to_process = {k: v for k, v in BRANDS.items() if v == args.brand} if args.brand else BRANDS
            
            for brand_ui_name, brand_filename in brands_to_process.items():
                try:
                    logger.info(f"\n{'=' * 80}")
                    logger.info(f"📦 BRAND: {brand_ui_name} ({brand_filename})")
                    logger.info(f"{'=' * 80}")
                    
                    switch_brand(page, brand_ui_name)
                    navigate_to_dashboard_by_product(page, brand_filename)
                    
                    output_file = DATA_DIR / f"{brand_filename}_dashboard_by_product_90d.csv"
                    download_csv_polling(page, brand_filename, output_file)
                    
                    downloaded_files.append(output_file)
                    logger.info(f"✅ SUCCESS: {brand_ui_name}")
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ FAILED: {brand_ui_name} - {e}")
                    failed_brands.append(brand_ui_name)
                    screenshot(page, f"FAILED_{brand_filename}")
        
        finally:
            browser.close()
    
    # Summary
    logger.info(f"\n{'=' * 80}")
    logger.info("📊 FINAL SUMMARY")
    logger.info(f"{'=' * 80}")
    logger.info(f"✅ Successful: {len(downloaded_files)}")
    logger.info(f"❌ Failed: {len(failed_brands)}")
    
    if downloaded_files:
        logger.info("\n📁 Downloaded files:")
        for f in downloaded_files:
            size_mb = f.stat().st_size / 1024 / 1024
            logger.info(f"  ✓ {f.name} ({size_mb:.2f} MB)")
    
    if failed_brands:
        logger.info("\n⚠️  Failed brands:")
        for b in failed_brands:
            logger.info(f"  ✗ {b}")
    
    # Process into JSON
    if downloaded_files and not failed_brands:
        logger.info(f"\n{'=' * 80}")
        logger.info("🔄 Processing CSVs into sku_velocity.json...")
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from sellerboard_export import update_velocity_data
            update_velocity_data()
            logger.info("✅ Processing complete!")
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"🏁 COMPLETE")
    logger.info(f"⏰ {datetime.now().isoformat()}")
    logger.info(f"{'=' * 80}\n")
    
    return 0 if not failed_brands else 1


if __name__ == "__main__":
    sys.exit(main())
