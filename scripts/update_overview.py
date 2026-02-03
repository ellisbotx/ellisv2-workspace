#!/usr/bin/env python3
"""
Updates the Trifecta Overview page with real sales data from Amazon SP-API.
Pulls last 30 days of sales metrics for all brands.
"""

import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
import html as html_escape

CREDS_DIR = Path("/Users/ellisbot/.openclaw/workspace/credentials")
HTML_FILE = Path("/Users/ellisbot/.openclaw/workspace/trifecta/index.html")
DATA_FILE = Path("/Users/ellisbot/.openclaw/workspace/data/overview_data.json")
REORDER_REPORT_FILE = Path("/Users/ellisbot/.openclaw/workspace/data/reorder_report.json")

BRANDS = {
    "cardplug": {"name": "Card Plug", "creds_file": "cardplug_amazon.txt"},
    "blackowned": {"name": "Black Owned", "creds_file": "blackowned_amazon.txt"},
    "kinfolk": {"name": "Kinfolk", "creds_file": "kinfolk_amazon.txt"}
}

MARKETPLACE_ID = "ATVPDKIKX0DER"

def load_credentials(brand_key):
    creds_file = CREDS_DIR / BRANDS[brand_key]["creds_file"]
    creds = {}
    if creds_file.exists():
        for line in creds_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                creds[key.strip()] = value.strip()
    return creds

def get_access_token(creds):
    response = requests.post('https://api.amazon.com/auth/o2/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': creds['REFRESH_TOKEN'],
        'client_id': creds['CLIENT_ID'],
        'client_secret': creds['CLIENT_SECRET']
    })
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def get_sales_metrics(access_token, days=30, start_date=None, end_date=None):
    """Get sales metrics for a period"""
    headers = {'x-amz-access-token': access_token, 'Content-Type': 'application/json'}
    
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=days)
    
    url = f"https://sellingpartnerapi-na.amazon.com/sales/v1/orderMetrics?marketplaceIds={MARKETPLACE_ID}&interval={start_date.strftime('%Y-%m-%d')}T00:00:00Z--{end_date.strftime('%Y-%m-%d')}T23:59:59Z&granularity=Total"
    
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        payload = data.get('payload', [{}])[0]
        return {
            'units': payload.get('unitCount', 0),
            'orders': payload.get('orderCount', 0),
            'revenue': payload.get('totalSales', {}).get('amount', 0),
            'avg_price': payload.get('averageUnitPrice', {}).get('amount', 0)
        }
    return {'units': 0, 'orders': 0, 'revenue': 0, 'avg_price': 0}

def get_yesterday_metrics(access_token):
    """Get yesterday's sales metrics"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today - timedelta(days=1)
    yesterday_end = today - timedelta(seconds=1)
    
    return get_sales_metrics(access_token, start_date=yesterday_start, end_date=yesterday_end)

def pull_all_data():
    """Pull sales data for all brands"""
    print("Pulling sales data for overview...")
    
    current_period = {}
    yesterday_data = {}
    
    for brand_key, brand_info in BRANDS.items():
        print(f"  {brand_info['name']}...")
        
        creds = load_credentials(brand_key)
        if not creds:
            continue
            
        token = get_access_token(creds)
        if not token:
            continue
        
        # Current 30 days
        current = get_sales_metrics(token, 30)
        current_period[brand_key] = current
        
        # Yesterday
        yesterday = get_yesterday_metrics(token)
        yesterday_data[brand_key] = yesterday
    
    # Calculate totals - 30 days
    total_revenue = sum(b.get('revenue', 0) for b in current_period.values())
    total_units = sum(b.get('units', 0) for b in current_period.values())
    total_orders = sum(b.get('orders', 0) for b in current_period.values())
    
    # Calculate totals - yesterday
    yesterday_revenue = sum(b.get('revenue', 0) for b in yesterday_data.values())
    yesterday_units = sum(b.get('units', 0) for b in yesterday_data.values())
    yesterday_orders = sum(b.get('orders', 0) for b in yesterday_data.values())
    
    # Estimate profit (rough 30% margin until Sellerboard gives us real data)
    estimated_margin = 0.30
    estimated_profit = total_revenue * estimated_margin
    yesterday_profit = yesterday_revenue * estimated_margin
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'period_days': 30,
        'totals': {
            'revenue': round(total_revenue, 2),
            'profit': round(estimated_profit, 2),
            'margin': round(estimated_margin * 100, 1),
            'units': total_units,
            'orders': total_orders
        },
        'yesterday': {
            'revenue': round(yesterday_revenue, 2),
            'profit': round(yesterday_profit, 2),
            'units': yesterday_units,
            'orders': yesterday_orders
        },
        'brands': {},
        'brands_yesterday': {}
    }
    
    for brand_key, metrics in current_period.items():
        brand_profit = metrics['revenue'] * estimated_margin
        data['brands'][brand_key] = {
            'name': BRANDS[brand_key]['name'],
            'revenue': round(metrics['revenue'], 2),
            'profit': round(brand_profit, 2),
            'units': metrics['units'],
            'margin': round(estimated_margin * 100, 1)
        }
    
    for brand_key, metrics in yesterday_data.items():
        brand_profit = metrics['revenue'] * estimated_margin
        data['brands_yesterday'][brand_key] = {
            'name': BRANDS[brand_key]['name'],
            'revenue': round(metrics['revenue'], 2),
            'profit': round(brand_profit, 2),
            'units': metrics['units']
        }
    
    # Save data
    DATA_FILE.write_text(json.dumps(data, indent=2))
    print(f"✓ Data saved to {DATA_FILE}")
    
    return data

def build_inventory_alerts_html(max_items: int = 5) -> str:
    """Build dynamic inventory runway alerts from reorder_report.json.

    Rules:
      - Red: runway_days < 60
      - Yellow: 60 <= runway_days < 90
      - Show top N most urgent items (lowest runway first)
    """
    if not REORDER_REPORT_FILE.exists():
        return (
            '<div class="alert-item">'
            '<div class="alert-dot green"></div>'
            '<span><strong>No alerts:</strong> Reorder report not found</span>'
            '</div>'
        )

    report = json.loads(REORDER_REPORT_FILE.read_text())

    items = []
    for brand_key, brand in (report.get("brands") or {}).items():
        brand_name = brand.get("brand") or brand.get("name") or brand_key
        for sku in brand.get("skus", []) or []:
            runway = sku.get("runway_days")
            if runway is None:
                continue
            try:
                runway_val = float(runway)
            except (TypeError, ValueError):
                continue
            if runway_val >= 90:
                continue

            fba_qty = sku.get("fba_qty", 0)
            name = sku.get("name") or sku.get("sku") or "(Unnamed SKU)"

            items.append(
                {
                    "brand": brand_name,
                    "name": name,
                    "fba_qty": int(fba_qty) if isinstance(fba_qty, (int, float)) else fba_qty,
                    "runway_days": runway_val,
                }
            )

    items.sort(key=lambda x: x["runway_days"])
    items = items[:max_items]

    if not items:
        return (
            '<div class="alert-item">'
            '<div class="alert-dot green"></div>'
            '<span><strong>No alerts:</strong> Inventory runway is healthy</span>'
            '</div>'
        )

    lines = []
    for it in items:
        dot_class = "red" if it["runway_days"] < 60 else "yellow"
        prefix = "Urgent Reorder" if dot_class == "red" else "Watch"

        name = html_escape.escape(str(it["name"]))
        brand = html_escape.escape(str(it["brand"]))
        units = it["fba_qty"]
        runway_days = int(round(it["runway_days"]))

        lines.append(
            "\n".join(
                [
                    '<div class="alert-item">',
                    f'    <div class="alert-dot {dot_class}"></div>',
                    f'    <span><strong>{prefix}:</strong> {name} ({brand}) — {units} units, {runway_days} days runway</span>',
                    '</div>',
                ]
            )
        )

    return "\n".join(lines)


def inject_alerts_into_html(html: str) -> str:
    """Replace ALERTS_START/END block in overview HTML with generated alerts."""
    alerts_html = build_inventory_alerts_html(max_items=5)
    block = f"<!-- ALERTS_START -->\n{alerts_html}\n            <!-- ALERTS_END -->"

    # Keep indentation stable by including the surrounding whitespace in the pattern.
    pattern = r"<!-- ALERTS_START -->.*?<!-- ALERTS_END -->"
    if re.search(pattern, html, flags=re.DOTALL):
        return re.sub(pattern, block, html, flags=re.DOTALL)

    # If markers are missing, do nothing (avoid breaking the page)
    return html


def update_html(data):
    """Update the overview HTML with real data"""
    html = HTML_FILE.read_text()
    
    t = data['totals']
    y = data.get('yesterday', {})
    
    # Update total sales with yesterday
    html = re.sub(
        r'(<div class="metric-label">Total Sales</div>\s*<div class="metric-value">)\$[\d,]+</div>\s*<div class="metric-change[^"]*">[^<]*<[^>]*>[^<]*</div>',
        f'''\\1${t["revenue"]:,.0f}</div>
            <div class="metric-change" style="color:#8b949e;">
                Yesterday: <strong style="color:#58a6ff;">${y.get("revenue", 0):,.0f}</strong> ({y.get("units", 0)} units)
            </div>''',
        html
    )
    
    # Update total profit with yesterday
    html = re.sub(
        r'(<div class="metric-label">Total Profit</div>\s*<div class="metric-value profit">)\$[\d,]+</div>\s*<div class="metric-change[^"]*">[^<]*<[^>]*>[^<]*</div>',
        f'''\\1${t["profit"]:,.0f}</div>
            <div class="metric-change" style="color:#8b949e;">
                Yesterday: <strong style="color:#3fb950;">${y.get("profit", 0):,.0f}</strong> (est)
            </div>''',
        html
    )
    
    # Update timestamp
    now = datetime.now()
    html = re.sub(
        r'Data last updated:.*?•',
        f'Data last updated: {now.strftime("%B %d, %Y at %I:%M %p")} CT •',
        html
    )
    
    # Update period
    html = re.sub(
        r'Last <span>30 Days</span> • \w+ \d{4}',
        f'Last <span>30 Days</span> • {now.strftime("%B %Y")}',
        html
    )

    # Update dynamic inventory runway alerts
    html = inject_alerts_into_html(html)
    
    HTML_FILE.write_text(html)
    print(f"✓ Overview HTML updated")

def main():
    print("=" * 50)
    print("OVERVIEW DATA UPDATE")
    print("=" * 50)
    
    data = pull_all_data()
    update_html(data)
    
    print(f"\nSummary (Last 30 Days):")
    print(f"  Revenue: ${data['totals']['revenue']:,.0f}")
    print(f"  Profit (est): ${data['totals']['profit']:,.0f}")
    print(f"  Units: {data['totals']['units']:,}")

if __name__ == "__main__":
    main()
