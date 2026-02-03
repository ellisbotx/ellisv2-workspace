#!/usr/bin/env python3
"""
ASIN Suppression Checker v2
Simple check: Does the ASIN show YOUR card game product? 
Yes = Active, No = Suppressed. That's it.
"""

import csv
import json
import time
import random
import argparse
import sys
import re
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: Missing dependencies. Run: pip3 install requests beautifulsoup4")
    sys.exit(1)

# Paths
WORKSPACE = Path("/Users/ellisbot/.openclaw/workspace")
MASTER_LIST = WORKSPACE / "data" / "asin_master_list.csv"
TRACKER = WORKSPACE / "data" / "suppression_tracker.csv"
RESULTS_JSON = WORKSPACE / "data" / "last_check_results.json"
DASHBOARD = WORKSPACE / "trifecta" / "index.html"

# Amazon search URL
AMAZON_SEARCH_URL = "https://www.amazon.com/s?k={asin}"

# Headers to look like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Keywords that indicate YOUR card game product is showing
CARD_GAME_KEYWORDS = [
    "card game", "party game", "cards", "deck", "playing cards",
    "conversation", "game for", "adult game", "drinking game",
    "family game", "couples game", "date night", "icebreaker",
    "card games", "games for adults", "party games"
]


def load_master_list():
    """Load ASINs from the master list CSV."""
    asins = []
    if not MASTER_LIST.exists():
        print(f"ERROR: Master list not found at {MASTER_LIST}")
        sys.exit(1)
    
    with open(MASTER_LIST, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            asins.append({
                "asin": row.get("ASIN", "").strip(),
                "name": row.get("Name", "Unknown").strip(),
                "brand": row.get("Brand", "Unknown").strip()
            })
    
    # Filter out empty ASINs
    asins = [a for a in asins if a["asin"]]
    print(f"Loaded {len(asins)} ASINs from master list")
    return asins


def check_asin(asin_info, session):
    """
    Simple check: Does a card game show up when searching this ASIN?
    Yes = Active, No = Suppressed. That's it.
    """
    asin = asin_info["asin"]
    url = AMAZON_SEARCH_URL.format(asin=asin)
    
    try:
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()
        
        # Check for CAPTCHA
        if "enter the characters you see below" in page_text or "robot" in page_text:
            return {
                "asin": asin,
                "name": asin_info["name"],
                "brand": asin_info["brand"],
                "status": "Error",
                "notes": "CAPTCHA - retry later"
            }
        
        # Check for "no results"
        if "no results for" in page_text:
            return {
                "asin": asin,
                "name": asin_info["name"],
                "brand": asin_info["brand"],
                "status": "Suppressed",
                "notes": "No results found"
            }
        
        # Simple check: Do ANY card game keywords appear?
        has_card_game = any(kw in page_text for kw in CARD_GAME_KEYWORDS)
        
        if has_card_game:
            return {
                "asin": asin,
                "name": asin_info["name"],
                "brand": asin_info["brand"],
                "status": "Active",
                "notes": "Card game found"
            }
        else:
            return {
                "asin": asin,
                "name": asin_info["name"],
                "brand": asin_info["brand"],
                "status": "Suppressed",
                "notes": "No card game found in results"
            }
            
    except requests.exceptions.Timeout:
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
    
    # Format timestamp
    now = datetime.now()
    timestamp = now.strftime("%b %d, %Y at %-I:%M %p").replace(" 0", " ")
    footer_timestamp = now.strftime("%B %d, %Y at %-I:%M %p CT").replace(" 0", " ")
    
    # Health percentage
    health_pct = int((active / total) * 100) if total > 0 else 100
    
    # Read dashboard
    with open(DASHBOARD, 'r') as f:
        html = f.read()
    
    # Update "X of X ASINs visible"
    html = re.sub(
        r'<p>\d+ of \d+ ASINs visible in Amazon search</p>',
        f'<p>{active} of {total} ASINs visible in Amazon search</p>',
        html
    )
    
    # Update "Last checked" timestamp
    html = re.sub(
        r'Last checked: <span>[^<]+</span>',
        f'Last checked: <span>{timestamp}</span>',
        html
    )
    
    # Update health percent
    html = re.sub(
        r'<div class="health-percent[^"]*">\d+%</div>',
        f'<div class="health-percent">{health_pct}%</div>',
        html
    )
    
    # Update brand counts
    html = re.sub(
        r'<div class="brand-pill-count"><span>\d+</span> Black Owned</div>',
        f'<div class="brand-pill-count"><span>{black_owned}</span> Black Owned</div>',
        html
    )
    html = re.sub(
        r'<div class="brand-pill-count"><span>\d+</span> Card Plug</div>',
        f'<div class="brand-pill-count"><span>{card_plug}</span> Card Plug</div>',
        html
    )
    html = re.sub(
        r'<div class="brand-pill-count"><span>\d+</span> Kinfolk</div>',
        f'<div class="brand-pill-count"><span>{kinfolk}</span> Kinfolk</div>',
        html
    )
    
    # Update footer timestamp
    html = re.sub(
        r'Data last updated: [^•]+•',
        f'Data last updated: {footer_timestamp} •',
        html
    )
    
    # Update suppression badge count
    if suppressed == 0:
        html = re.sub(
            r'<div class="suppression-count-badge[^"]*">\d+ Issues?</div>',
            '<div class="suppression-count-badge clear">0 Issues</div>',
            html
        )
    else:
        html = re.sub(
            r'<div class="suppression-count-badge[^"]*">\d+ Issues?</div>',
            f'<div class="suppression-count-badge">{suppressed} Issue{"s" if suppressed != 1 else ""}</div>',
            html
        )
    
    # Update status message
    if suppressed == 0:
        html = re.sub(
            r'<h3[^>]*>[^<]+</h3>\s*<p>\d+ of \d+',
            f'<h3>All Clear</h3>\n                    <p>{active} of {total}',
            html
        )
    else:
        html = re.sub(
            r'<h3[^>]*>[^<]+</h3>\s*<p>\d+ of \d+',
            f'<h3 class="warning">{suppressed} Suppressed</h3>\n                    <p>{active} of {total}',
            html
        )
    
    # Write updated dashboard
    with open(DASHBOARD, 'w') as f:
        f.write(html)
    
    print(f"Dashboard updated: {DASHBOARD}")


def print_summary(results):
    """Print summary."""
    total = len(results)
    active = sum(1 for r in results if r["status"] == "Active")
    suppressed = sum(1 for r in results if r["status"] == "Suppressed")
    errors = sum(1 for r in results if r["status"] == "Error")
    
    print("\n" + "="*50)
    print("ASIN CHECK SUMMARY")
    print("="*50)
    print(f"Total:      {total}")
    print(f"Active:     {active}")
    print(f"Suppressed: {suppressed}")
    print(f"Errors:     {errors}")
    print("="*50)
    
    if suppressed > 0:
        print("\n🚨 SUPPRESSED:")
        for r in results:
            if r["status"] == "Suppressed":
                print(f"  {r['asin']} - {r['name']} ({r['brand']})")
    
    return {"total": total, "active": active, "suppressed": suppressed, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Check ASINs")
    parser.add_argument("--limit", type=int, help="Limit ASINs to check")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests")
    args = parser.parse_args()
    
    print(f"ASIN Checker - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    asins = load_master_list()
    
    if args.limit:
        asins = asins[:args.limit]
        print(f"Limited to {args.limit} ASINs")
    
    session = requests.Session()
    results = []
    
    print(f"\nChecking {len(asins)} ASINs...")
    
    for i, asin_info in enumerate(asins, 1):
        print(f"[{i}/{len(asins)}] {asin_info['asin']} ({asin_info['name']})...", end=" ", flush=True)
        
        result = check_asin(asin_info, session)
        results.append(result)
        
        emoji = "✅" if result["status"] == "Active" else "🚨" if result["status"] == "Suppressed" else "❌"
        print(f"{emoji} {result['status']}")
        
        if i < len(asins):
            time.sleep(args.delay + random.uniform(0, 1))
    
    save_results(results)
    update_dashboard(results)
    print_summary(results)


if __name__ == "__main__":
    main()
