#!/usr/bin/env python3
"""
Unified Inventory Tracker for All Brands
Pulls FBA inventory from Amazon SP-API for Card Plug, Black Owned, and Kinfolk.
Generates dashboard data and alerts.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data")
CREDS_DIR = Path("/Users/ellisbot/.openclaw/workspace/credentials")
DASHBOARD_FILE = DATA_DIR / "inventory_dashboard.json"
AWD_OVERRIDE_FILE = DATA_DIR / "awd_inventory.json"  # Manual AWD input

BRANDS = {
    "cardplug": {
        "name": "Card Plug",
        "creds_file": "cardplug_amazon.txt"
    },
    "blackowned": {
        "name": "Black Owned", 
        "creds_file": "blackowned_amazon.txt"
    },
    "kinfolk": {
        "name": "Kinfolk",
        "creds_file": "kinfolk_amazon.txt"
    }
}

MARKETPLACE_ID = "ATVPDKIKX0DER"

# Stock thresholds
THRESHOLD_LOW = 50
THRESHOLD_MEDIUM = 100

# =============================================================================
# CREDENTIALS & API
# =============================================================================

def load_credentials(brand_key):
    """Load credentials for a brand"""
    creds_file = CREDS_DIR / BRANDS[brand_key]["creds_file"]
    creds = {}
    
    if creds_file.exists():
        for line in creds_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip()
    
    return creds

def get_access_token(creds):
    """Get Amazon access token"""
    response = requests.post('https://api.amazon.com/auth/o2/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': creds['REFRESH_TOKEN'],
        'client_id': creds['CLIENT_ID'],
        'client_secret': creds['CLIENT_SECRET']
    })
    
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def get_fba_inventory(access_token):
    """Get all FBA inventory"""
    headers = {
        'x-amz-access-token': access_token,
        'Content-Type': 'application/json'
    }
    
    all_items = []
    next_token = None
    
    while True:
        url = f"https://sellingpartnerapi-na.amazon.com/fba/inventory/v1/summaries?details=true&granularityType=Marketplace&granularityId={MARKETPLACE_ID}&marketplaceIds={MARKETPLACE_ID}"
        if next_token:
            url += f"&nextToken={next_token}"
        
        resp = requests.get(url, headers=headers)
        
        if resp.status_code != 200:
            break
            
        data = resp.json()
        items = data.get('payload', {}).get('inventorySummaries', [])
        all_items.extend(items)
        
        next_token = data.get('pagination', {}).get('nextToken')
        if not next_token:
            break
    
    return all_items

# =============================================================================
# AWD OVERRIDE (Manual Input)
# =============================================================================

def load_awd_overrides():
    """Load manual AWD inventory data"""
    if AWD_OVERRIDE_FILE.exists():
        return json.loads(AWD_OVERRIDE_FILE.read_text())
    return {}

def get_combined_quantity(sku, fba_qty, awd_data):
    """Get FBA + AWD combined quantity"""
    awd_qty = awd_data.get(sku, 0)
    return fba_qty + awd_qty, awd_qty

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def pull_all_inventory():
    """Pull inventory for all brands"""
    timestamp = datetime.now().isoformat()
    awd_data = load_awd_overrides()
    
    dashboard = {
        "timestamp": timestamp,
        "brands": {},
        "alerts": {
            "out_of_stock": [],
            "low_stock": [],
            "medium_stock": []
        },
        "totals": {
            "total_skus": 0,
            "out_of_stock": 0,
            "low_stock": 0,
            "medium_stock": 0,
            "healthy": 0,
            "total_fba_units": 0,
            "total_awd_units": 0
        }
    }
    
    for brand_key, brand_info in BRANDS.items():
        print(f"Pulling {brand_info['name']}...")
        
        creds = load_credentials(brand_key)
        if not creds:
            print(f"  ⚠ No credentials found for {brand_info['name']}")
            continue
        
        access_token = get_access_token(creds)
        if not access_token:
            print(f"  ⚠ Failed to get access token for {brand_info['name']}")
            continue
        
        items = get_fba_inventory(access_token)
        print(f"  ✓ Found {len(items)} SKUs")
        
        brand_data = {
            "name": brand_info["name"],
            "total_skus": len(items),
            "out_of_stock": 0,
            "low_stock": 0,
            "medium_stock": 0,
            "healthy": 0,
            "total_fba_units": 0,
            "total_awd_units": 0,
            "items": []
        }
        
        for item in items:
            sku = item.get('sellerSku', 'N/A')
            asin = item.get('asin', 'N/A')
            name = item.get('productName', 'Unknown')
            fba_qty = item.get('totalQuantity', 0)
            
            # Get AWD override if exists
            combined_qty, awd_qty = get_combined_quantity(sku, fba_qty, awd_data)
            
            brand_data["total_fba_units"] += fba_qty
            brand_data["total_awd_units"] += awd_qty
            
            item_record = {
                "sku": sku,
                "asin": asin,
                "name": name[:60],
                "fba_qty": fba_qty,
                "awd_qty": awd_qty,
                "total_qty": combined_qty
            }
            
            # Categorize based on COMBINED quantity (FBA + AWD)
            if combined_qty == 0:
                brand_data["out_of_stock"] += 1
                dashboard["alerts"]["out_of_stock"].append({
                    "brand": brand_info["name"],
                    **item_record
                })
            elif combined_qty < THRESHOLD_LOW:
                brand_data["low_stock"] += 1
                dashboard["alerts"]["low_stock"].append({
                    "brand": brand_info["name"],
                    **item_record
                })
            elif combined_qty < THRESHOLD_MEDIUM:
                brand_data["medium_stock"] += 1
                dashboard["alerts"]["medium_stock"].append({
                    "brand": brand_info["name"],
                    **item_record
                })
            else:
                brand_data["healthy"] += 1
            
            brand_data["items"].append(item_record)
        
        # Sort items by quantity (lowest first)
        brand_data["items"].sort(key=lambda x: x["total_qty"])
        
        dashboard["brands"][brand_key] = brand_data
        
        # Update totals
        dashboard["totals"]["total_skus"] += brand_data["total_skus"]
        dashboard["totals"]["out_of_stock"] += brand_data["out_of_stock"]
        dashboard["totals"]["low_stock"] += brand_data["low_stock"]
        dashboard["totals"]["medium_stock"] += brand_data["medium_stock"]
        dashboard["totals"]["healthy"] += brand_data["healthy"]
        dashboard["totals"]["total_fba_units"] += brand_data["total_fba_units"]
        dashboard["totals"]["total_awd_units"] += brand_data["total_awd_units"]
    
    # Sort alerts by quantity
    dashboard["alerts"]["out_of_stock"].sort(key=lambda x: x["total_qty"])
    dashboard["alerts"]["low_stock"].sort(key=lambda x: x["total_qty"])
    dashboard["alerts"]["medium_stock"].sort(key=lambda x: x["total_qty"])
    
    # Save dashboard data
    DASHBOARD_FILE.write_text(json.dumps(dashboard, indent=2))
    print(f"\n✓ Dashboard data saved to {DASHBOARD_FILE}")
    
    # Update the HTML dashboard with embedded data
    import subprocess
    subprocess.run(["python3", "/Users/ellisbot/.openclaw/workspace/scripts/update_inventory_html.py"], capture_output=True)
    
    return dashboard

def generate_report(dashboard):
    """Generate text report for messaging"""
    t = dashboard["totals"]
    
    lines = [
        "📦 INVENTORY REPORT",
        f"As of: {datetime.fromisoformat(dashboard['timestamp']).strftime('%Y-%m-%d %H:%M')}",
        "",
        "═══ PORTFOLIO SUMMARY ═══",
        f"Total SKUs: {t['total_skus']}",
        f"🔴 Out of Stock: {t['out_of_stock']}",
        f"🟠 Low (<50): {t['low_stock']}",
        f"🟡 Medium (50-99): {t['medium_stock']}",
        f"🟢 Healthy (100+): {t['healthy']}",
        "",
        f"FBA Units: {t['total_fba_units']:,}",
        f"AWD Units: {t['total_awd_units']:,}",
        ""
    ]
    
    # Brand breakdown
    for brand_key, brand in dashboard["brands"].items():
        lines.append(f"═══ {brand['name'].upper()} ═══")
        lines.append(f"SKUs: {brand['total_skus']} | 🔴{brand['out_of_stock']} 🟠{brand['low_stock']} 🟡{brand['medium_stock']} 🟢{brand['healthy']}")
        lines.append("")
    
    # Critical alerts (low stock, excluding out of stock puzzles/art)
    critical = [a for a in dashboard["alerts"]["low_stock"] if a["total_qty"] > 0]
    if critical:
        lines.append("⚠️ LOW STOCK ALERTS:")
        for alert in critical[:10]:  # Top 10
            lines.append(f"  {alert['total_qty']:3} | {alert['brand']}: {alert['name'][:40]}")
        if len(critical) > 10:
            lines.append(f"  ... and {len(critical) - 10} more")
    
    return "\n".join(lines)

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 50)
    print("UNIFIED INVENTORY TRACKER")
    print("=" * 50)
    print()
    
    dashboard = pull_all_inventory()
    
    print()
    print(generate_report(dashboard))
    
    # If --report flag, just print the report (for cron messaging)
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        print("\n--- REPORT FOR MESSAGING ---")
        print(generate_report(dashboard))
