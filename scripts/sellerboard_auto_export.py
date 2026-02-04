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
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

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
DOWNLOADS_DIR = DATA_DIR / "downloads"
PROFILE_DIR = DATA_DIR / "chromium_profile"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

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
    """Fetch Sellerboard credentials from local credential file."""
    try:
        creds_path = Path("/Users/ellisbot/.openclaw/workspace/.credentials.json")
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        username = creds['sellerboard']['username']
        password = creds['sellerboard']['password']
        return username, password
    except Exception as e:
        logger.error(f"Failed to get credentials from {creds_path}: {e}")
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
    # NOTE: keep selectors tight; avoid nuking normal UI elements that happen to
    # contain substrings like "modal" or "overlay" in class names.
    try:
        removed = page.evaluate('''
            () => {
                const backdrops = document.querySelectorAll(
                    '.modal-backdrop, .cdk-overlay-backdrop, [data-backdrop], [class*="backdrop"]'
                );
                backdrops.forEach(el => el.remove());

                // Hide common dialog containers
                const dialogs = document.querySelectorAll(
                    '.modal[role="dialog"], .modal.show, [role="dialog"], [aria-modal="true"]'
                );
                dialogs.forEach(el => {
                    try { el.style.display = 'none'; } catch (e) {}
                });

                return backdrops.length + dialogs.length;
            }
        ''')
        if removed > 0:
            logger.info(f"Removed {removed} modal elements via JavaScript")
            popup_closed = True
            time.sleep(0.5)
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
    """Switch to a specific brand using the account/brand switcher.

    Sellerboard's UI varies: sometimes it's a <select>, other times it's a
    dropdown menu in the header. This function tries both paths.
    """
    brands_regex = "|".join([re.escape(b) for b in BRANDS.keys()])

    for attempt in range(max_retries):
        try:
            logger.info(f"Switching to brand: {brand_name} (attempt {attempt + 1}/{max_retries})...")

            close_popups(page, aggressive=True)

            # Strategy 1: native <select>
            select_loc = page.locator('select[name*="brand" i], select[name*="account" i], select[name*="store" i]').first
            try:
                if select_loc.count() and select_loc.is_visible(timeout=1500):
                    select_loc.select_option(label=brand_name)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    take_screenshot(page, f"04_brand_switched_{brand_name.lower().replace(' ', '_')}")
                    logger.info(f"✓ Switched to {brand_name} (select)")
                    return True
            except Exception:
                pass

            # Strategy 2: Click the account/brand dropdown in top-right header
            # The dropdown shows EMAIL ADDRESS (e.g., srgrier45@gmail.com), not brand name
            logger.info("Looking for account dropdown in header (shows email)...")
            
            # Click the element showing the email address
            try:
                # Try to find the element with @gmail.com in the header
                email_button = page.locator('header:has-text("@gmail.com")').locator('button, a').first
                if email_button.is_visible(timeout=5000):
                    logger.info("Found account dropdown (contains @gmail.com)")
                    email_button.click(timeout=5000)
                    time.sleep(1.5)  # Let dropdown menu appear
                    dropdown_opened = True
                else:
                    raise Exception("Email dropdown not visible")
            except Exception as e:
                logger.warning(f"Could not find account dropdown: {e}")
                raise Exception(f"Could not find/open account dropdown in header: {e}")
            
            # Now click the target brand INSIDE the dropdown menu
            logger.info(f"Looking for '{brand_name}' in dropdown menu...")
            
            # Wait for menu to be visible, then click the brand name
            try:
                # Look for the brand name text in any visible dropdown/menu
                brand_item = page.locator(f'text={brand_name}').first
                if brand_item.is_visible(timeout=5000):
                    logger.info(f"Found '{brand_name}' in dropdown menu")
                    brand_item.click(timeout=5000)
                else:
                    raise Exception(f"Brand '{brand_name}' not visible in menu")
            except Exception as e:
                logger.error(f"Could not find/click '{brand_name}' in dropdown: {e}")
                raise Exception(f"Could not find/click '{brand_name}' in dropdown menu: {e}")

            time.sleep(2)
            page.wait_for_load_state("networkidle", timeout=15000)
            take_screenshot(page, f"04_brand_switched_{brand_name.lower().replace(' ', '_')}")
            
            # MANDATORY verification - confirm the header now shows the target brand
            logger.info(f"Verifying brand switch to {brand_name}...")
            header_text_selectors = [
                f'header button:has-text("{brand_name}")',
                f'header a:has-text("{brand_name}")',
                f'header:has-text("{brand_name}")',
            ]
            verified = False
            for sel in header_text_selectors:
                try:
                    if page.locator(sel).first.is_visible(timeout=3000):
                        verified = True
                        logger.info(f"✓ VERIFIED: Brand switched to {brand_name}")
                        break
                except:
                    continue
            
            if not verified:
                raise Exception(f"Brand verification FAILED - header does not show '{brand_name}' after switch attempt")
            
            return True

        except Exception as e:
            logger.warning(f"Brand switch attempt {attempt + 1} failed: {e}")
            take_screenshot(page, f"error_brand_switch_{attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
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


def wait_for_downloading_modal(page, appear_timeout_ms: int = 15000) -> Tuple[bool, Optional[str]]:
    """Best-effort wait for Sellerboard 'Downloading / Your file is being prepared' modal.

    Returns (appeared, selector_that_appeared).

    NOTE: We intentionally do NOT wait for the modal to disappear. In the current
    Sellerboard flow, we want to click "Email me when ready" and immediately
    move on to the next brand (no local download waiting).
    """
    modal_selectors = [
        'text=/Your file is being prepared/i',
        'text=/Downloading/i',
        'text=/Preparing/i',
        'css=.modal:has-text("Downloading")',
        'css=.modal:has-text("prepared")',
        'css=[class*="modal"]:has-text("Downloading")',
        'css=[class*="modal"]:has-text("prepared")',
    ]

    for sel in modal_selectors:
        try:
            page.wait_for_selector(sel, state="visible", timeout=appear_timeout_ms)
            logger.info("✓ Downloading modal appeared")
            return True, sel
        except Exception:
            continue

    return False, None


def click_email_me_when_ready_and_close(page, appear_timeout_ms: int = 15000) -> bool:
    """When the Downloading modal appears, click "Email me when ready", close it, and return.

    Returns True if the modal appeared and we attempted the click.
    """
    appeared, _ = wait_for_downloading_modal(page, appear_timeout_ms=appear_timeout_ms)
    if not appeared:
        return False

    # 1) Click the "Email me when ready" button (best-effort)
    email_btn_selectors = [
        'button:has-text("Email me when ready")',
        'button:has-text("Email me")',
        'text=/Email me when ready/i',
    ]

    clicked = False
    for sel in email_btn_selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() and btn.is_visible(timeout=2000):
                btn.click(timeout=5000)
                clicked = True
                logger.info("✓ Clicked 'Email me when ready'")
                break
        except Exception:
            continue

    if not clicked:
        logger.warning("Downloading modal appeared, but could not find 'Email me when ready' button")

    # 2) Close the modal so it doesn't block next brand
    try:
        close_popups(page, aggressive=True)
    except Exception:
        pass

    # 3) Small settle time
    time.sleep(1)
    return True


def _wait_for_file_stable(path: Path, min_bytes: int = 1000, stable_secs: int = 3, timeout_secs: int = 60) -> bool:
    """Verify file exists, has min size, and stops growing for stable_secs."""
    start = time.time()
    last_size = -1
    last_change = time.time()

    while time.time() - start < timeout_secs:
        if path.exists():
            try:
                size = path.stat().st_size
            except FileNotFoundError:
                size = 0

            if size != last_size:
                last_size = size
                last_change = time.time()

            if size >= min_bytes and (time.time() - last_change) >= stable_secs:
                return True
        time.sleep(0.5)

    return False


def find_recent_download_file(since_ts: float, timeout_secs: int = 180, directory: Path = DOWNLOADS_DIR) -> Optional[Path]:
    """Fallback: poll downloads directory for a newly created file after since_ts.

    Sellerboard/Playwright sometimes saves downloads with UUID-like filenames (no .csv extension).
    """
    deadline = time.time() + timeout_secs
    best: Optional[Path] = None

    while time.time() < deadline:
        candidates = []
        for p in directory.iterdir():
            try:
                if not p.is_file():
                    continue
                # Skip temp/partial names
                if p.name.endswith('.crdownload') or p.name.endswith('.tmp'):
                    continue
                mtime = p.stat().st_mtime
                size = p.stat().st_size
            except FileNotFoundError:
                continue
            if mtime >= since_ts and size > 0:
                candidates.append((mtime, size, p))

        if candidates:
            candidates.sort(reverse=True)
            best = candidates[0][2]
            if _wait_for_file_stable(best, min_bytes=1000, stable_secs=3, timeout_secs=30):
                return best

        time.sleep(2)

    return best


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
        
        # Remove any modal/tooltips/backdrops that might block clicks
        page.evaluate('''
            () => {
                document.querySelectorAll(
                    '.modal-backdrop, [class*="modal-backdrop"], .newFeature, [data-tippy-root], [id^="tippy-"]'
                ).forEach(el => el.remove());
            }
        ''')
        time.sleep(0.5)
        
        # Use more specific selector
        page.locator('text="Dashboard by product"').click(timeout=10000)
        time.sleep(2)
        page.wait_for_load_state("networkidle", timeout=15000)
        wait_for_angular(page)
        
        take_screenshot(page, f"06_dashboard_by_product_{brand_filename}")
        
        # Set date range: last 90 days (inclusive), ending yesterday to avoid partial-day data.
        end_date = (datetime.now() - timedelta(days=1)).date()
        start_date = (end_date - timedelta(days=89))
        logger.info(f"Setting date range to {start_date} → {end_date} (last 90 days)...")
        
        # Fill date inputs (try multiple strategies)
        try:
            # Strategy 1: label → following input (most reliable)
            from_input = page.locator('xpath=//label[contains(normalize-space(.),"From")]/following::input[1]').first
            to_input = page.locator('xpath=//label[contains(normalize-space(.),"To")]/following::input[1]').first

            if from_input.count() == 0 or to_input.count() == 0:
                raise Exception("Label-based date inputs not found")

            from_input.click()
            from_input.fill(start_date.strftime("%m/%d/%Y"))
            to_input.click()
            to_input.fill(end_date.strftime("%m/%d/%Y"))

            # Trigger Angular update
            from_input.press("Tab")
            to_input.press("Tab")
            time.sleep(1)
            wait_for_angular(page)

            logger.info(f"Date range set: {start_date} to {end_date}")
        except Exception as e1:
            logger.warning(f"Could not set date range via labels: {e1}")
            try:
                # Strategy 2: first two visible text inputs on the page (fallback)
                inputs = page.locator('input[type="text"], input:not([type])').filter(has_not=page.locator('[disabled]'))
                from_input = inputs.nth(0)
                to_input = inputs.nth(1)
                from_input.click()
                from_input.fill(start_date.strftime("%m/%d/%Y"))
                to_input.click()
                to_input.fill(end_date.strftime("%m/%d/%Y"))
                from_input.press("Tab")
                to_input.press("Tab")
                time.sleep(1)
                wait_for_angular(page)
                logger.info(f"Date range set (fallback): {start_date} to {end_date}")
            except Exception as e2:
                logger.warning(f"Could not set date range (fallback): {e2}")
        
        take_screenshot(page, f"07_dates_set_{brand_filename}")
        
        # Select CSV format
        logger.info("Selecting CSV format...")
        try:
            # Clear any blocking popovers
            page.evaluate('''() => {
                document.querySelectorAll('[data-tippy-root], [id^="tippy-"]').forEach(el => el.remove());
            }''')
            csv_option = page.locator('text=".CSV"').or_(
                page.locator('text="CSV"')
            ).first
            csv_option.click(timeout=10000)
            time.sleep(1)
            wait_for_angular(page)
            logger.info("✓ CSV format selected")
        except Exception as e:
            logger.warning(f"CSV selection issue: {e}")
            # Fallback: click the underlying radio/input directly
            try:
                page.evaluate('''() => {
                    const el = document.querySelector('#exportFormatCsv, input#exportFormatCsv, input[name*="exportFormat" i][value*="csv" i]');
                    if (el) el.click();
                }''')
                time.sleep(1)
                wait_for_angular(page)
                logger.info("✓ CSV format selected (JS fallback)")
            except Exception as e2:
                logger.warning(f"CSV JS fallback failed: {e2}")
        
        take_screenshot(page, f"08_format_selected_{brand_filename}")

        # Set marketplace to Amazon.com only
        logger.info("Setting marketplace to Amazon.com only...")
        try:
            # Prefer clicking a visible label/text first
            amazon_label = page.locator('label:has-text("Amazon.com")').first
            amazon_text = page.locator('text=/Amazon\\.com/i').first

            if amazon_label.count() and amazon_label.is_visible(timeout=3000):
                amazon_label.click(timeout=5000)
            elif amazon_text.count() and amazon_text.is_visible(timeout=3000):
                amazon_text.click(timeout=5000)
            else:
                # Fallback: check a checkbox within the Amazon.com label
                page.locator('xpath=//label[contains(.,"Amazon.com")]//input[@type="checkbox"]').first.check(timeout=5000)
            time.sleep(1)
            wait_for_angular(page)
            logger.info("✓ Marketplace set (Amazon.com)")
        except Exception as e:
            logger.warning(f"Marketplace selection issue (continuing): {e}")

        # Ensure email delivery is ON
        logger.info("Ensuring 'Send to email' is ON (email delivery)...")
        try:
            cb = page.locator('xpath=//label[contains(.,"Send to email")]//input[@type="checkbox"]').first
            if cb.count() and cb.is_visible(timeout=3000):
                if not cb.is_checked():
                    cb.check(timeout=3000)
                    time.sleep(0.5)
                logger.info("✓ Email delivery enabled")
            else:
                # If we can't access the checkbox directly, try toggling via label
                send_label = page.locator('label:has-text("Send to email")').first
                if send_label.count() and send_label.is_visible(timeout=3000):
                    # Best-effort: click label to enable
                    send_label.click(timeout=3000)
                    time.sleep(0.5)
                    logger.info("✓ Email delivery enabled (label toggle)")
        except Exception as e:
            logger.warning(f"Could not confirm 'Send to email' on (continuing): {e}")

        take_screenshot(page, f"08b_marketplace_email_{brand_filename}")

        if dry_run:
            logger.info("DRY RUN: Skipping download")
            return None

        # Ensure any datepicker/popover overlays are closed so the Download button is clickable.
        try:
            page.keyboard.press("Escape")
            time.sleep(0.3)
            page.click('body', position={"x": 10, "y": 10}, timeout=1000)
            time.sleep(0.3)
        except Exception:
            pass
        close_popups(page, aggressive=True)

        # Verify button is enabled
        if not verify_button_enabled(page):
            raise Exception("Download button is not enabled (Angular validation failed)")

        # Trigger export with EMAIL delivery
        logger.info("Triggering export (email delivery)...")

        desired_path = DOWNLOADS_DIR / f"{brand_filename}_dashboard_by_product_90d.csv"
        # Remove any existing file to avoid confusing the stability check.
        try:
            if desired_path.exists():
                desired_path.unlink()
        except Exception:
            pass

        last_error = None
        for attempt in range(3):
            try:
                since_ts = time.time()

                # Click the primary submit button (often labeled Download/Export)
                clicked = False
                for sel in [
                    'button:has-text("Download")',
                    'button[type="submit"]:has-text("Download")',
                    'button[type="submit"]:has-text("Export")',
                    'button:has-text("Export")',
                    'button[type="submit"]',
                ]:
                    try:
                        btn = page.locator(sel).first
                        if btn.count() and btn.is_visible(timeout=1500):
                            btn.click(timeout=8000)
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    page.evaluate("""() => {
                        const btn = document.querySelector('button[type="submit"], button');
                        if (btn) btn.click();
                    }""")

                # Wait for "Downloading" modal and click "Email me when ready"
                time.sleep(2)  # Give modal time to appear
                
                # Look for the modal
                modal_appeared = False
                try:
                    modal = page.locator('text=/Your file is being prepared|Downloading/i').first
                    if modal.is_visible(timeout=10000):
                        modal_appeared = True
                        logger.info("✓ 'Downloading' modal appeared")
                except:
                    pass
                
                if modal_appeared:
                    # Click "Email me when ready"
                    email_clicked = False
                    for sel in ['button:has-text("Email me when ready")', 'button:has-text("Email me")']:
                        try:
                            btn = page.locator(sel).first
                            if btn.is_visible(timeout=3000):
                                btn.click(timeout=5000)
                                email_clicked = True
                                logger.info("✓ Clicked 'Email me when ready'")
                                break
                        except:
                            continue
                    
                    if not email_clicked:
                        logger.warning("Could not find 'Email me when ready' button, but proceeding...")
                    
                    # Close modal
                    try:
                        close_popups(page, aggressive=True)
                    except:
                        pass
                else:
                    logger.info("No modal appeared (export may have been triggered directly)")
                
                take_screenshot(page, f"09_export_triggered_{brand_filename}")
                logger.info(f"✓ Export triggered with email delivery for {brand_filename}")
                return None  # Return None since we're not downloading

            except Exception as e:
                last_error = e
                logger.warning(f"Export trigger attempt {attempt + 1} failed: {e}")
                take_screenshot(page, f"error_export_trigger_attempt_{attempt + 1}_{brand_filename}")
                if attempt < 2:
                    time.sleep(2)
                    continue

                if attempt < 2:
                    time.sleep(3)
                    wait_for_angular(page)
                    if not verify_button_enabled(page):
                        logger.error("Button became disabled, cannot retry")
                        break
                    continue
                break

        raise Exception(f"Failed to download export CSV. Last error: {last_error}")
        
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
    
    # Setup browser
    downloaded_files = []
    triggered_brands = []
    failed_brands = []

    with sync_playwright() as p:
        logger.info("Launching browser...")

        # Use a persistent context so we can force a stable downloads directory.
        # This improves reliability if Playwright misses the download event.
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=args.headless,
            slow_mo=250,
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True,
            downloads_path=str(DOWNLOADS_DIR),
        )

        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            # Navigate to reports and only log in if Sellerboard shows the login form.
            # This avoids hard-depending on an active 1Password CLI session when the
            # persistent Chromium profile is already authenticated.
            page.goto(REPORTS_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            needs_login = False
            try:
                page.wait_for_selector('input[type="password"]', timeout=5000)
                needs_login = True
            except Exception:
                needs_login = False

            if needs_login:
                logger.info("Login required; fetching credentials from 1Password...")
                try:
                    username, password = get_credentials()
                    logger.info(f"Retrieved credentials for: {username}")
                except Exception:
                    logger.error("Failed to get credentials from 1Password. Run `op signin` and retry.")
                    return 1

                login(page, username, password)
            else:
                logger.info("✓ Already logged in (reusing saved session)")

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
                        triggered_brands.append(brand_ui_name)
                        logger.info(f"✓ Successfully exported {brand_ui_name} (downloaded file)")
                    else:
                        raise Exception("Export did not produce a downloaded file")
                    
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
            context.close()
    
    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("EXPORT SUMMARY")
    logger.info(f"{'=' * 60}")
    logger.info(f"Triggered exports: {len(triggered_brands)}")
    logger.info(f"Downloaded files: {len(downloaded_files)}")
    logger.info(f"Failed exports: {len(failed_brands)}")
    
    if triggered_brands:
        logger.info("\nTriggered brands:")
        for b in triggered_brands:
            logger.info(f"  ✓ {b}")

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
