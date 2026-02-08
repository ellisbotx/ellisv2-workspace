#!/usr/bin/env python3
"""
ASIN Suppression Checker v3 - Browser Edition
Uses real browser automation to avoid detection.
Simple check: Does the ASIN show YOUR card game product? 
Yes = Active, No = Suppressed. That's it.
"""

import csv
import json
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Missing playwright. Run: pip3 install playwright && playwright install chromium")
    sys.exit(1)

# Paths
WORKSPACE = Path("/Users/ellisbot/.openclaw/workspace")
MASTER_LIST = WORKSPACE / "data" / "asin_master_list.csv"
TRACKER = WORKSPACE / "data" / "suppression_tracker.csv"
RESULTS_JSON = WORKSPACE / "data" / "last_check_results.json"
DASHBOARD = WORKSPACE / "trifecta" / "index.html"

# Amazon search URL
AMAZON_SEARCH_URL = "https://www.amazon.com/s?k={asin}"

# Keywords that indicate YOUR card game product is showing
CARD_GAME_KEYWORDS = [
    "card game", "party game", "cards", "deck", "playing cards",
    "conversation", "game for", "adult game", "drinking game",
    "family game", "couples game", "date night", "icebreaker",
    "card games", "games for adults", "party games"
]


def load_master_list():
    """Load the master ASIN list."""
    asins = []
    with open(MASTER_LIST, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asins.append({
                "asin": row.get("ASIN", "").strip(),
                "name": row.get("Name", "Unknown").strip(),
                "brand": row.get("Brand", "Unknown").strip()
            })
    return [a for a in asins if a["asin"]]  # Filter out empty ASINs


def check_asin_browser(browser, asin_info, delay=2):
    """
    Check a single ASIN using real browser.
    Returns dict with status and notes.
    """
    asin = asin_info["asin"]
    url = AMAZON_SEARCH_URL.format(asin=asin)
    
    try:
        # Create new page
        page = browser.new_page()
        
        # Navigate to Amazon search
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        
        # Wait a bit for content to load
        time.sleep(delay)
        
        # Get page text
        page_text = page.content().lower()
        
        # Check for "no results"
        if "no results for" in page_text or "did not match any products" in page_text:
            result = {
                "asin": asin,
                "name": asin_info["name"],
                "brand": asin_info["brand"],
                "status": "Suppressed",
                "notes": "No results found"
            }
        else:
            # Check if card game keywords appear
            has_card_game = any(kw in page_text for kw in CARD_GAME_KEYWORDS)
            
            if has_card_game:
                result = {
                    "asin": asin,
                    "name": asin_info["name"],
                    "brand": asin_info["brand"],
                    "status": "Active",
                    "notes": "Card game found"
                }
            else:
                result = {
                    "asin": asin,
                    "name": asin_info["name"],
                    "brand": asin_info["brand"],
                    "status": "Suppressed",
                    "notes": "No card game found in results"
                }
        
        page.close()
        return result
        
    except PlaywrightTimeout:
        return {
            "asin": asin,
            "name": asin_info["name"],
            "brand": asin_info["brand"],
            "status": "Error",
            "notes": "Timeout"
        }
    except Exception as e:
        return {
            "asin": asin,
            "name": asin_info["name"],
            "brand": asin_info["brand"],
            "status": "Error",
            "notes": f"Error: {str(e)[:50]}"
        }


def save_results(results):
    """Save results to CSV tracker and JSON file."""
    now = datetime.now().strftime("%Y-%m-%d")
    
    # Save to JSON
    with open(RESULTS_JSON, 'w') as f:
        json.dump({
            "checked_at": datetime.now().isoformat(),
            "total_checked": len(results),
            "results": results
        }, f, indent=2)
    
    # Save to CSV
    with open(TRACKER, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ASIN", "Name", "Brand", "Status", "Last Checked", "Notes"])
        for r in results:
            writer.writerow([
                r["asin"],
                r["name"],
                r["brand"],
                r["status"],
                now,
                r["notes"]
            ])
    
    print(f"\nResults saved to {TRACKER}")


def update_dashboard(results):
    """Update the Trifecta dashboard with latest check results."""
    if not DASHBOARD.exists():
        print("Dashboard not found, skipping update")
        return
    
    total = len(results)
    active = sum(1 for r in results if r["status"] == "Active")
    suppressed = sum(1 for r in results if r["status"] == "Suppressed")
    
    # Count by brand
    brand_counts = {}
    for r in results:
        brand = r["brand"]
        if brand not in brand_counts:
            brand_counts[brand] = 0
        brand_counts[brand] += 1
    
    black_owned = brand_counts.get("Black Owned", 0)
    card_plug = brand_counts.get("Card Plug", 0)
    kinfolk = brand_counts.get("Kinfolk", 0)
    
    # Read dashboard HTML
    html = DASHBOARD.read_text()
    
    # Update stats
    html = html.replace(
        '<h3 class="warning">3 Suppressed</h3>',
        f'<h3 class="warning">{suppressed} Suppressed</h3>'
    )
    html = html.replace(
        '163 of 166 ASINs visible in Amazon search',
        f'{active} of {total} ASINs visible in Amazon search'
    )
    
    # Update timestamp
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p CT")
    import re
    html = re.sub(
        r'Last checked: [^<]+',
        f'Last checked: {now}',
        html
    )
    
    # Write back
    DASHBOARD.write_text(html)
    print(f"Dashboard updated: {DASHBOARD}")


def post_to_discord(results, summary):
    """Post results to Discord #reports and #alerts channels."""
    try:
        # Import the discord utilities
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from discord_utils import post_report, post_alert
        
        # Post summary to #reports
        summary_msg = f"""📊 **Daily ASIN Check Complete**

✅ Active: **{summary['active']}**
🚨 Suppressed: **{summary['suppressed']}**
❌ Errors: **{summary['errors']}**
📦 Total: **{summary['total']}**

Dashboard: <https://ellisbot.local/trifecta/>"""
        
        if post_report(summary_msg, silent=True):
            print("Posted summary to #reports")
        
        # Post alerts if suppressions found
        if summary['suppressed'] > 0:
            suppressed_list = [r for r in results if r["status"] == "Suppressed"]
            
            alert_msg = f"""🚨 **{summary['suppressed']} ASIN Suppression{'s' if summary['suppressed'] != 1 else ''} Detected**

"""
            for r in suppressed_list:
                alert_msg += f"• **{r['name']}** ({r['brand']})\n  ASIN: `{r['asin']}`\n  {r['notes']}\n\n"
            
            alert_msg += "Check <https://ellisbot.local/trifecta/> for details."
            
            if post_alert(alert_msg):
                print("Posted alert to #alerts")
    
    except Exception as e:
        print(f"Failed to post to Discord: {e}")


def main():
    parser = argparse.ArgumentParser(description="Check ASINs for suppression using browser automation")
    parser.add_argument("--limit", type=int, help="Limit number of ASINs to check (for testing)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between checks in seconds")
    args = parser.parse_args()
    
    print("ASIN Checker (Browser Edition) - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("-" * 50)
    
    # Load ASINs
    asins = load_master_list()
    print(f"Loaded {len(asins)} ASINs from master list\n")
    
    if args.limit:
        asins = asins[:args.limit]
        print(f"Testing mode: checking first {args.limit} ASINs\n")
    
    # Start browser
    print(f"Checking {len(asins)} ASINs...")
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for i, asin_info in enumerate(asins, 1):
            result = check_asin_browser(browser, asin_info, delay=args.delay)
            results.append(result)
            
            # Print progress
            status_emoji = "✅" if result["status"] == "Active" else ("⚠️" if result["status"] == "Suppressed" else "❌")
            print(f"[{i}/{len(asins)}] {result['asin']} ({result['name']})... {status_emoji} {result['status']}")
        
        browser.close()
    
    # Summary
    total = len(results)
    active = sum(1 for r in results if r["status"] == "Active")
    suppressed = sum(1 for r in results if r["status"] == "Suppressed")
    errors = sum(1 for r in results if r["status"] == "Error")
    
    print("\n" + "=" * 50)
    print("ASIN CHECK SUMMARY")
    print("=" * 50)
    print(f"Total: {total}")
    print(f"Active: {active}")
    print(f"Suppressed: {suppressed}")
    print(f"Errors: {errors}")
    print("=" * 50)
    
    # Save results
    save_results(results)
    update_dashboard(results)
    
    # Alert if suppressions found
    if suppressed > 0:
        print(f"\n⚠️  {suppressed} ASIN(s) suppressed:")
        for r in results:
            if r["status"] == "Suppressed":
                print(f"  - {r['asin']} ({r['name']}) - {r['notes']}")
    
    # Post to Discord
    post_to_discord(results, {"total": total, "active": active, "suppressed": suppressed, "errors": errors})
    
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
