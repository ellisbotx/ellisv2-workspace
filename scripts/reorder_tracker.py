#!/usr/bin/env python3
"""
Reorder Tracker - Velocity-Based Inventory Alerts
Calculates days of runway based on 90-day sales velocity.
Generates reorder alerts and liquidation candidates.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data")
CREDS_DIR = Path("/Users/ellisbot/.openclaw/workspace/credentials")
OUTPUT_FILE = DATA_DIR / "reorder_report.json"

# Business rules
LEAD_TIME_DAYS = 75
SAFETY_BUFFER_DAYS = 90  # Total runway needed before reorder
MOQ = 500
VELOCITY_PERIOD_DAYS = 90

# Liquidation thresholds
LIQUIDATE_VELOCITY_THRESHOLD = 1.0  # Less than 1 unit/day
LIQUIDATE_RUNWAY_THRESHOLD = 180    # More than 180 days of stock

BRANDS = {
    "cardplug": {"name": "Card Plug", "creds_file": "cardplug_amazon.txt"},
    "blackowned": {"name": "Black Owned", "creds_file": "blackowned_amazon.txt"},
    "kinfolk": {"name": "Kinfolk", "creds_file": "kinfolk_amazon.txt"}
}

MARKETPLACE_ID = "ATVPDKIKX0DER"

# =============================================================================
# API HELPERS
# =============================================================================

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

def get_fba_inventory(access_token):
    """Get current FBA inventory"""
    headers = {'x-amz-access-token': access_token, 'Content-Type': 'application/json'}
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
    
    return {item['sellerSku']: item for item in all_items}

def get_orders_with_items(access_token, days=90):
    """Get orders and aggregate by SKU"""
    headers = {'x-amz-access-token': access_token, 'Content-Type': 'application/json'}
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get all orders
    all_orders = []
    next_token = None
    
    while True:
        url = f"https://sellingpartnerapi-na.amazon.com/orders/v0/orders?MarketplaceIds={MARKETPLACE_ID}&CreatedAfter={start_date.isoformat()}Z&OrderStatuses=Shipped"
        if next_token:
            url += f"&NextToken={next_token}"
        
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            break
            
        data = resp.json()
        orders = data.get('payload', {}).get('Orders', [])
        all_orders.extend(orders)
        
        next_token = data.get('payload', {}).get('NextToken')
        if not next_token or len(all_orders) > 5000:  # Safety limit
            break
    
    # Get order items for each order and aggregate by SKU
    sku_sales = defaultdict(int)
    
    for order in all_orders:
        order_id = order['AmazonOrderId']
        items_url = f"https://sellingpartnerapi-na.amazon.com/orders/v0/orders/{order_id}/orderItems"
        
        resp = requests.get(items_url, headers=headers)
        if resp.status_code == 200:
            items = resp.json().get('payload', {}).get('OrderItems', [])
            for item in items:
                sku = item.get('SellerSKU', '')
                qty = item.get('QuantityOrdered', 0)
                if sku:
                    sku_sales[sku] += qty
    
    return dict(sku_sales)

def get_sales_aggregate(access_token, days=90):
    """Get aggregate sales metrics (faster but less granular)"""
    headers = {'x-amz-access-token': access_token, 'Content-Type': 'application/json'}
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    url = f"https://sellingpartnerapi-na.amazon.com/sales/v1/orderMetrics?marketplaceIds={MARKETPLACE_ID}&interval={start_date.strftime('%Y-%m-%d')}T00:00:00Z--{end_date.strftime('%Y-%m-%d')}T23:59:59Z&granularity=Total"
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        payload = data.get('payload', [{}])[0]
        return {
            'units': payload.get('unitCount', 0),
            'orders': payload.get('orderCount', 0),
            'revenue': payload.get('totalSales', {}).get('amount', 0)
        }
    return {'units': 0, 'orders': 0, 'revenue': 0}

# =============================================================================
# VELOCITY CALCULATION
# =============================================================================

def calculate_velocity_from_inventory(inventory_data, sales_aggregate, days=90):
    """
    Estimate per-SKU velocity based on inventory turnover.
    This is an approximation when we can't get per-SKU sales data quickly.
    """
    total_units = sales_aggregate.get('units', 0)
    total_skus = len(inventory_data)
    
    if total_skus == 0:
        return {}
    
    # Simple approach: distribute sales proportionally to inventory
    # (items with more inventory likely sell more)
    total_inventory = sum(item.get('totalQuantity', 0) for item in inventory_data.values())
    
    velocity = {}
    for sku, item in inventory_data.items():
        inv_qty = item.get('totalQuantity', 0)
        if total_inventory > 0:
            # Proportional estimate
            estimated_sales = (inv_qty / total_inventory) * total_units
        else:
            estimated_sales = 0
        
        velocity[sku] = {
            'daily_velocity': round(estimated_sales / days, 2),
            'period_sales': int(estimated_sales),
            'method': 'proportional_estimate'
        }
    
    return velocity

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def analyze_brand(brand_key):
    """Analyze a single brand for reorder needs"""
    brand_name = BRANDS[brand_key]["name"]
    print(f"\nAnalyzing {brand_name}...")
    
    creds = load_credentials(brand_key)
    if not creds:
        print(f"  ⚠ No credentials for {brand_name}")
        return None
    
    access_token = get_access_token(creds)
    if not access_token:
        print(f"  ⚠ Failed to get token for {brand_name}")
        return None
    
    # Get inventory
    inventory = get_fba_inventory(access_token)
    print(f"  ✓ {len(inventory)} SKUs in inventory")
    
    # Get aggregate sales
    sales = get_sales_aggregate(access_token, VELOCITY_PERIOD_DAYS)
    print(f"  ✓ {sales['units']:,} units sold in {VELOCITY_PERIOD_DAYS} days (${sales['revenue']:,.0f})")
    
    # Calculate velocity estimates
    velocity = calculate_velocity_from_inventory(inventory, sales, VELOCITY_PERIOD_DAYS)
    
    # Build SKU analysis
    skus = []
    reorder_needed = []
    liquidate_candidates = []
    
    for sku, inv_item in inventory.items():
        qty = inv_item.get('totalQuantity', 0)
        name = inv_item.get('productName', 'Unknown')[:50]
        asin = inv_item.get('asin', '')
        
        vel = velocity.get(sku, {})
        daily_vel = vel.get('daily_velocity', 0)
        
        # Calculate runway
        if daily_vel > 0:
            runway_days = qty / daily_vel
        else:
            runway_days = 9999  # Infinite runway if no sales
        
        sku_data = {
            'sku': sku,
            'asin': asin,
            'name': name,
            'fba_qty': qty,
            'daily_velocity': daily_vel,
            'runway_days': round(runway_days, 1),
            'reorder_needed': runway_days < SAFETY_BUFFER_DAYS and daily_vel > 0
        }
        
        skus.append(sku_data)
        
        # Check if reorder needed
        if sku_data['reorder_needed']:
            sku_data['urgency'] = 'critical' if runway_days < 30 else 'soon' if runway_days < 60 else 'normal'
            reorder_needed.append(sku_data)
        
        # Check if liquidation candidate
        if daily_vel < LIQUIDATE_VELOCITY_THRESHOLD and qty > 0 and runway_days > LIQUIDATE_RUNWAY_THRESHOLD:
            liquidate_candidates.append(sku_data)
    
    # Sort by runway (most urgent first)
    reorder_needed.sort(key=lambda x: x['runway_days'])
    liquidate_candidates.sort(key=lambda x: x['runway_days'], reverse=True)
    
    return {
        'brand': brand_name,
        'brand_key': brand_key,
        'total_skus': len(skus),
        'sales_90d': sales,
        'reorder_count': len(reorder_needed),
        'liquidate_count': len(liquidate_candidates),
        'reorder_needed': reorder_needed,
        'liquidate_candidates': liquidate_candidates[:20],  # Top 20
        'skus': sorted(skus, key=lambda x: x['runway_days'])
    }

def generate_full_report():
    """Generate full reorder report for all brands"""
    print("=" * 50)
    print("REORDER TRACKER")
    print(f"Safety buffer: {SAFETY_BUFFER_DAYS} days | MOQ: {MOQ}")
    print("=" * 50)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'config': {
            'lead_time_days': LEAD_TIME_DAYS,
            'safety_buffer_days': SAFETY_BUFFER_DAYS,
            'moq': MOQ,
            'velocity_period_days': VELOCITY_PERIOD_DAYS
        },
        'brands': {},
        'all_reorders': [],
        'all_liquidate': [],
        'summary': {
            'total_skus': 0,
            'total_reorder_needed': 0,
            'total_liquidate_candidates': 0
        }
    }
    
    for brand_key in BRANDS:
        result = analyze_brand(brand_key)
        if result:
            report['brands'][brand_key] = result
            report['all_reorders'].extend([{**r, 'brand': result['brand']} for r in result['reorder_needed']])
            report['all_liquidate'].extend([{**l, 'brand': result['brand']} for l in result['liquidate_candidates']])
            report['summary']['total_skus'] += result['total_skus']
            report['summary']['total_reorder_needed'] += result['reorder_count']
            report['summary']['total_liquidate_candidates'] += result['liquidate_count']
    
    # Sort all reorders by urgency
    report['all_reorders'].sort(key=lambda x: x['runway_days'])
    report['all_liquidate'].sort(key=lambda x: x['runway_days'], reverse=True)
    
    # Save report
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    print(f"\n✓ Report saved to {OUTPUT_FILE}")
    
    return report

def print_report(report):
    """Print human-readable report"""
    print("\n" + "=" * 60)
    print("📦 REORDER REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    s = report['summary']
    print(f"\nTotal SKUs: {s['total_skus']}")
    print(f"Need Reorder: {s['total_reorder_needed']}")
    print(f"Liquidate Candidates: {s['total_liquidate_candidates']}")
    
    # Reorder alerts
    reorders = report['all_reorders']
    if reorders:
        print(f"\n🔴 REORDER NOW ({len(reorders)} items):")
        print("-" * 60)
        for item in reorders[:15]:
            urgency_icon = "🚨" if item.get('urgency') == 'critical' else "⚠️" if item.get('urgency') == 'soon' else "📋"
            print(f"{urgency_icon} {item['runway_days']:5.0f}d | {item['fba_qty']:4} units | {item['daily_velocity']:.1f}/day | {item['brand']}: {item['name'][:35]}")
        if len(reorders) > 15:
            print(f"   ... and {len(reorders) - 15} more")
    else:
        print("\n✅ No immediate reorders needed")
    
    # Liquidation candidates
    liquidate = report['all_liquidate'][:10]
    if liquidate:
        print(f"\n🐌 SLOW SELLERS / LIQUIDATE CANDIDATES:")
        print("-" * 60)
        for item in liquidate:
            print(f"   {item['runway_days']:5.0f}d | {item['fba_qty']:4} units | {item['daily_velocity']:.1f}/day | {item['brand']}: {item['name'][:35]}")

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    report = generate_full_report()
    print_report(report)
