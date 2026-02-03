#!/usr/bin/env python3
"""Automated Sellerboard export downloader using browser automation.

This script:
1. Logs into Sellerboard using 1Password credentials
2. Switches between 3 brands (Black Owned, Card Plug, Kinfolk)
3. Downloads "Dashboard by product" CSV exports for last 90 days
4. Processes the exports into sku_velocity.json

Usage:
  python3 sellerboard_auto_export.py [--dry-run] [--no-process]

Options:
  --dry-run: Run without downloading (test navigation only)
  --no-process: Download CSVs but don't process into JSON
  --headless: Run browser in headless mode (default: headed for debugging)
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Try to import playwright, provide helpful error if missing
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Playwright not installed. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

# Import the processing function from existing script
sys.path.insert(0, str(Path(__file__).parent))
from sellerboard_export import update_velocity_data

# Configuration
DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")
LOG_FILE = DATA_DIR / "auto_export.log"
SCREENSHOT_DIR = DATA_DIR / "screenshots"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Brands to export (UI name -> filename prefix)
BRANDS = {
    "Summary Dashboard": "blackowned",  # srgrier45 (Black Owned)
    "CardPlug": "cardplug",
    "Kinfolk": "kinfolk",
}

# URLs
LOGIN_URL = "https://app.sellerboard.com/login"
REPORTS_URL = "https://app.sellerboard.com/en/export"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_credentials():
    """Fetch Sellerboard credentials from 1Password."""
    try:
        result = subprocess.run(
            ["op", "item", "get", "sellerboard", "--fields", "label=username,label=password", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        creds = json.loads(result.stdout)
        username = next(c["value"] for c in creds if c["label"] == "username")
        password = next(c["value"] for c in creds if c["label"] == "password")
        return username, password
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get credentials from 1Password: {e}")
        logger.error(f"Make sure you're authenticated: op signin")
        raise
    except Exception as e:
        logger.error(f"Error parsing credentials: {e}")
        raise


def take_screenshot(page, name: str):
    """Take a screenshot for debugging."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOT_DIR / f"{timestamp}_{name}.png"
    page.screenshot(path=str(filepath))
    logger.info(f"Screenshot saved: {filepath}")
    return filepath


def close_popups(page, aggressive=False):
    """Close any modal popups or overlays."""
    popup_closed = False
    
    # First: Remove modal backdrops via JavaScript (most reliable)
    try:
        removed = page.evaluate('''
            () => {
                const backdrops = document.querySelectorAll('.modal-backdrop, [class*="modal-backdrop"], [class*="overlay"]');
                backdrops.forEach(el => el.remove());
                const modals = document.querySelectorAll('.modal, [class*="modal"]');
                modals.forEach(el => {
                    if (el.style.display !== 'none') {
                        el.style.display = 'none';
                    }
                });
                return backdrops.length + modals.length;
            }
        ''')
        if removed > 0:
            logger.info(f"Removed {removed} modal elements via JavaScript")
            popup_closed = True
            time.sleep(1)
    except Exception as e:
        logger.debug(f"JavaScript modal removal failed: {e}")
    
    # Second: Try clicking close buttons
    popup_selectors = [
        'button:has-text("×")',
        'button[aria-label="Close"]',
        'button.close',
        '.close',
        '[class*="modal"] button:has-text("Close")',
        '[class*="popup"] button:has-text("Close")',
        'button:has-text("Got it")',
        'button:has-text("OK")',
        'button:has-text("Dismiss")',
        'button:has-text("Skip")',
        'button:has-text("No thanks")',
    ]
    
    for selector in popup_selectors:
        try:
            elements = page.locator(selector).all()
            for element in elements:
                if element.is_visible(timeout=1000):
                    element.click()
                    popup_closed = True
                    logger.info(f"Closed popup with selector: {selector}")
                    time.sleep(1)
                    break
            if popup_closed and not aggressive:
                break
        except:
            continue
    
    # Third: ESC key to dismiss modals
    if aggressive or popup_closed:
        try:
            page.keyboard.press("Escape")
            time.sleep(0.5)
            logger.info("Pressed ESC to dismiss modals")
        except:
            pass
    
    return popup_closed


def login(page, username: str, password: str, max_retries: int = 3):
    """Login to Sellerboard with retry logic."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Navigating to app (will redirect to login) (attempt {attempt + 1}/{max_retries})...")
            # Navigate to reports page - it will redirect to login if not authenticated
            page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            
            # Wait for login form (should appear after redirect)
            logger.info("Waiting for login form...")
            page.wait_for_selector('input[type="email"], input[name="email"], input#email, input[type="text"]', timeout=15000)
            
            take_screenshot(page, "01_login_page")
            
            # Fill in credentials
            logger.info(f"Entering credentials for {username}...")
            # Find email input - try multiple strategies
            email_selectors = [
                'input[placeholder*="mail" i]',
                'input[type="text"]:first-of-type',
                'input[name*="mail" i]',
                'input[id*="mail" i]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_input = page.locator(selector).first
                    if email_input.is_visible(timeout=2000):
                        email_input.fill(username)
                        email_filled = True
                        logger.info(f"Filled email with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_filled:
                raise Exception("Could not find email input field")
            
            # Find password input
            password_input = page.locator('input[type="password"]').first
            password_input.fill(password)
            logger.info("Filled password")
            
            take_screenshot(page, "02_credentials_filled")
            
            # Click login button
            logger.info("Clicking login button...")
            login_buttons = [
                'button:has-text("Continue")',
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")'
            ]
            
            button_clicked = False
            for selector in login_buttons:
                try:
                    button = page.locator(selector).first
                    if button.is_visible(timeout=2000):
                        button.click()
                        button_clicked = True
                        logger.info(f"Clicked button with selector: {selector}")
                        break
                except:
                    continue
            
            if not button_clicked:
                raise Exception("Could not find login button")
            
            # Wait for navigation to complete
            logger.info("Waiting for login to complete...")
            page.wait_for_load_state("networkidle", timeout=30000)
            
            # Check if we're logged in (look for account/dashboard elements)
            page.wait_for_selector('a[href*="dashboard"], button:has-text("Account"), [class*="user"], [class*="account"]', timeout=15000)
            
            take_screenshot(page, "03_logged_in")
            logger.info("✓ Login successful!")
            return True
            
        except PlaywrightTimeout as e:
            logger.warning(f"Login attempt {attempt + 1} timed out: {e}")
            take_screenshot(page, f"error_login_attempt_{attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            take_screenshot(page, "error_login_failed")
            raise
    
    return False


def switch_brand(page, brand_name: str, max_retries: int = 3):
    """Switch to a specific brand using the dropdown."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Switching to brand: {brand_name} (attempt {attempt + 1}/{max_retries})...")
            
            # Look for brand switcher dropdown (usually in top-right)
            # Common selectors: dropdown, select, or button that opens a menu
            brand_selectors = [
                'select[name*="brand"], select[name*="account"], select[name*="store"]',
                'button:has-text("' + brand_name + '")',
                '[class*="brand"], [class*="account"], [class*="store"]'
            ]
            
            # Try to find and click the dropdown
            dropdown_clicked = False
            for selector in brand_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        element.click()
                        dropdown_clicked = True
                        logger.info(f"Clicked dropdown with selector: {selector}")
                        break
                except:
                    continue
            
            if not dropdown_clicked:
                # Try finding by text content
                logger.info("Trying to find brand switcher by text...")
                page.locator(f'text={brand_name}').first.click(timeout=5000)
            
            time.sleep(2)  # Wait for brand switch to complete
            page.wait_for_load_state("networkidle", timeout=15000)
            
            take_screenshot(page, f"04_brand_switched_{brand_name.lower().replace(' ', '_')}")
            logger.info(f"✓ Switched to {brand_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Brand switch attempt {attempt + 1} failed: {e}")
            take_screenshot(page, f"error_brand_switch_{attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                logger.error(f"Failed to switch to {brand_name} after {max_retries} attempts")
                return False
    
    return False


def wait_for_angular(page, timeout_ms=5000):
    """Wait for AngularJS to finish digest cycle."""
    try:
        page.wait_for_function(
            """() => {
                if (typeof angular === 'undefined') return true;
                try {
                    const rootElement = document.querySelector('[ng-app]') || document;
                    const injector = angular.element(rootElement).injector();
                    if (!injector) return true;
                    const $browser = injector.get('$browser');
                    return $browser.deferredFns.length === 0;
                } catch (e) {
                    return true;
                }
            }""",
            timeout=timeout_ms
        )
        logger.debug("Angular digest cycle complete")
    except Exception as e:
        logger.warning(f"Angular check timed out: {e}")


def verify_button_enabled(page, timeout_ms=10000):
    """Wait for download button to be enabled."""
    try:
        page.wait_for_function(
            """() => {
                const btn = document.querySelector('button[type="submit"]');
                return btn && !btn.disabled && !btn.hasAttribute('disabled');
            }""",
            timeout=timeout_ms
        )
        logger.debug("Download button is enabled")
        return True
    except Exception as e:
        logger.error(f"Download button not enabled: {e}")
        return False


def export_dashboard_by_product(page, brand_filename: str, dry_run: bool = False):
    """Navigate to Dashboard by product report and download CSV (IMPROVED)."""
    try:
        logger.info(f"Navigating to Reports page...")
        page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        wait_for_angular(page)
        
        # Close any modal popups
        try:
            close_button = page.locator('button:has-text("×"), button[aria-label="Close"]').first
            if close_button.is_visible(timeout=2000):
                close_button.click()
                time.sleep(1)
        except:
            pass
        
        take_screenshot(page, f"05_reports_page_{brand_filename}")
        
        # Click "Dashboard by product" report
        logger.info("Clicking 'Dashboard by product' report...")
        
        # Remove any modal backdrops that might block the click
        page.evaluate('''
            () => {
                document.querySelectorAll('.modal-backdrop, [class*="modal-backdrop"], .newFeature').forEach(el => el.remove());
            }
        ''')
        time.sleep(0.5)
        
        # Use more specific selector
        page.locator('text="Dashboard by product"').click(timeout=10000)
        time.sleep(2)
        page.wait_for_load_state("networkidle", timeout=15000)
        wait_for_angular(page)
        
        take_screenshot(page, f"06_dashboard_by_product_{brand_filename}")
        
        # Set date range (last 90 days)
        logger.info("Setting date range to last 90 days...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Fill date inputs (try multiple strategies)
        try:
            # Strategy 1: Direct fill
            from_input = page.locator('input').filter(has_text="From").or_(
                page.locator('input[placeholder*="From" i]')
            ).first
            to_input = page.locator('input').filter(has_text="To").or_(
                page.locator('input[placeholder*="To" i]')
            ).first
            
            from_input.fill(start_date.strftime("%m/%d/%Y"))
            to_input.fill(end_date.strftime("%m/%d/%Y"))
            
            # Trigger Angular update
            from_input.press("Tab")
            to_input.press("Tab")
            time.sleep(1)
            wait_for_angular(page)
            
            logger.info(f"Date range set: {start_date.date()} to {end_date.date()}")
        except Exception as e:
            logger.warning(f"Could not set date range: {e}")
        
        take_screenshot(page, f"07_dates_set_{brand_filename}")
        
        # Select CSV format
        logger.info("Selecting CSV format...")
        try:
            csv_option = page.locator('text=".CSV"').or_(
                page.locator('text="CSV"')
            ).first
            csv_option.click()
            time.sleep(1)
            wait_for_angular(page)
            logger.info("✓ CSV format selected")
        except Exception as e:
            logger.warning(f"CSV selection issue: {e}")
        
        take_screenshot(page, f"08_format_selected_{brand_filename}")
        
        if dry_run:
            logger.info("DRY RUN: Skipping download")
            return None
        
        # Verify button is enabled
        if not verify_button_enabled(page):
            raise Exception("Download button is not enabled (Angular validation failed)")
        
        # Setup download handler BEFORE clicking
        output_file = DATA_DIR / f"{brand_filename}_dashboard_by_product_90d.csv"
        
        logger.info("Initiating download...")
        
        # Try download with multiple strategies
        download = None
        for attempt in range(3):
            try:
                with page.expect_download(timeout=60000) as download_info:
                    # Strategy 1: Playwright click
                    try:
                        page.click('button[type="submit"]:has-text("Download")', timeout=5000)
                        logger.info(f"Clicked download button (Playwright, attempt {attempt + 1})")
                    except:
                        # Strategy 2: JavaScript click
                        page.evaluate("""() => {
                            const btn = document.querySelector('button[type="submit"]');
                            if (btn) btn.click();
                        }""")
                        logger.info(f"Clicked download button (JavaScript, attempt {attempt + 1})")
                
                download = download_info.value
                break  # Success!
                
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    take_screenshot(page, f"error_download_attempt_{attempt + 1}_{brand_filename}")
                    time.sleep(3)
                    # Re-verify button state
                    wait_for_angular(page)
                    if not verify_button_enabled(page):
                        logger.error("Button became disabled, cannot retry")
                        raise
                else:
                    raise
        
        if not download:
            raise Exception("Failed to capture download after 3 attempts")
        
        # Save the download
        download.save_as(output_file)
        
        # Verify file
        if output_file.stat().st_size < 1000:
            raise Exception(f"Downloaded file too small: {output_file.stat().st_size} bytes")
        
        logger.info(f"✓ Downloaded: {output_file} ({output_file.stat().st_size} bytes)")
        take_screenshot(page, f"09_download_complete_{brand_filename}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Export failed for {brand_filename}: {e}")
        take_screenshot(page, f"error_export_{brand_filename}")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Test navigation without downloading")
    parser.add_argument("--no-process", action="store_true", help="Download only, don't process into JSON")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--brand", choices=list(BRANDS.values()), help="Export only one brand")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Sellerboard Auto Export Started")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 60)
    
    # Get credentials
    try:
        username, password = get_credentials()
        logger.info(f"Retrieved credentials for: {username}")
    except Exception as e:
        logger.error("Failed to get credentials. Exiting.")
        return 1
    
    # Setup browser
    downloaded_files = []
    failed_brands = []
    
    with sync_playwright() as p:
        logger.info("Launching browser...")
        browser = p.chromium.launch(headless=args.headless, slow_mo=500)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        page = context.new_page()
        
        try:
            # Login
            login(page, username, password)
            
            # Filter brands if specified
            brands_to_export = {k: v for k, v in BRANDS.items() if v == args.brand} if args.brand else BRANDS
            
            # Export each brand
            for brand_ui_name, brand_filename in brands_to_export.items():
                try:
                    logger.info(f"\n{'=' * 60}")
                    logger.info(f"Processing brand: {brand_ui_name} ({brand_filename})")
                    logger.info(f"{'=' * 60}")
                    
                    # Switch brand
                    if not switch_brand(page, brand_ui_name):
                        logger.error(f"Failed to switch to {brand_ui_name}, skipping...")
                        failed_brands.append(brand_ui_name)
                        continue
                    
                    # Export data
                    output_file = export_dashboard_by_product(page, brand_filename, dry_run=args.dry_run)
                    
                    if output_file:
                        downloaded_files.append(output_file)
                        logger.info(f"✓ Successfully exported {brand_ui_name}")
                    
                    # Brief pause between brands
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Failed to export {brand_ui_name}: {e}")
                    failed_brands.append(brand_ui_name)
                    continue
            
        except Exception as e:
            logger.error(f"Critical error during automation: {e}")
            take_screenshot(page, "error_critical")
            return 1
        finally:
            logger.info("Closing browser...")
            browser.close()
    
    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("EXPORT SUMMARY")
    logger.info(f"{'=' * 60}")
    logger.info(f"Successful exports: {len(downloaded_files)}")
    logger.info(f"Failed exports: {len(failed_brands)}")
    
    if downloaded_files:
        logger.info("\nDownloaded files:")
        for f in downloaded_files:
            logger.info(f"  ✓ {f}")
    
    if failed_brands:
        logger.info("\nFailed brands:")
        for b in failed_brands:
            logger.info(f"  ✗ {b}")
    
    # Process into JSON
    if not args.dry_run and not args.no_process and downloaded_files:
        logger.info(f"\n{'=' * 60}")
        logger.info("Processing CSVs into sku_velocity.json...")
        logger.info(f"{'=' * 60}")
        try:
            velocity_data = update_velocity_data()
            logger.info("✓ Processing complete!")
        except Exception as e:
            logger.error(f"Failed to process CSVs: {e}")
            return 1
    
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Sellerboard Auto Export Complete")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"{'=' * 60}\n")
    
    return 0 if not failed_brands else 1


if __name__ == "__main__":
    sys.exit(main())
