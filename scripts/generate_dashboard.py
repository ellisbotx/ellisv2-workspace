#!/usr/bin/env python3
"""
Generates the full Trifecta dashboard HTML files with embedded data.
Combines inventory, reorder/runway, and overview data.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data")
TRIFECTA_DIR = Path("/Users/ellisbot/.openclaw/workspace/trifecta")

def load_json(filename):
    filepath = DATA_DIR / filename
    if filepath.exists():
        return json.loads(filepath.read_text())
    return {}

def generate_inventory_html():
    """Generate the inventory dashboard with embedded data"""
    
    inventory = load_json("inventory_dashboard.json")
    reorder = load_json("reorder_report.json")
    
    # Merge runway data into inventory
    if reorder and inventory:
        for brand_key, brand_data in reorder.get('brands', {}).items():
            if brand_key in inventory.get('brands', {}):
                # Create SKU lookup for runway
                runway_lookup = {s['sku']: s for s in brand_data.get('skus', [])}
                
                # Add runway to inventory items
                for item in inventory['brands'][brand_key].get('items', []):
                    sku = item['sku']
                    if sku in runway_lookup:
                        item['daily_velocity'] = runway_lookup[sku].get('daily_velocity', 0)
                        item['runway_days'] = runway_lookup[sku].get('runway_days', 9999)
    
    # Get all items sorted by runway
    all_items_by_runway = []
    for brand_key, brand_data in inventory.get('brands', {}).items():
        for item in brand_data.get('items', []):
            item['brand'] = brand_data.get('name', brand_key)
            item['brand_key'] = brand_key
            all_items_by_runway.append(item)
    
    all_items_by_runway.sort(key=lambda x: x.get('runway_days', 9999))
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inventory | Trifecta</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #e6edf3;
            min-height: 100vh;
            padding: 24px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }}
        .logo {{
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #58a6ff, #a371f7, #f778ba);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .nav-tabs {{ display: flex; gap: 8px; }}
        .nav-tab {{
            padding: 8px 16px;
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #8b949e;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
        }}
        .nav-tab:hover {{ background: #30363d; color: #e6edf3; }}
        .nav-tab.active {{ background: #388bfd; border-color: #388bfd; color: #fff; }}
        
        .notice {{
            background: rgba(56, 139, 253, 0.1);
            border: 1px solid rgba(56, 139, 253, 0.3);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 24px;
            font-size: 13px;
            color: #8b949e;
        }}
        .notice strong {{ color: #58a6ff; }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-bottom: 32px;
        }}
        .summary-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        .summary-value {{ font-size: 32px; font-weight: 700; margin-bottom: 4px; }}
        .summary-label {{ font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; }}
        .summary-value.red {{ color: #f85149; }}
        .summary-value.orange {{ color: #f0883e; }}
        .summary-value.yellow {{ color: #d29922; }}
        .summary-value.green {{ color: #3fb950; }}
        
        .section {{ margin-bottom: 32px; }}
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: #8b949e;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .brand-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        .brand-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
        }}
        .brand-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #30363d;
        }}
        .brand-name {{ font-size: 18px; font-weight: 600; }}
        .brand-name.cardplug {{ color: #a371f7; }}
        .brand-name.blackowned {{ color: #f0883e; }}
        .brand-name.kinfolk {{ color: #58a6ff; }}
        
        .status-row {{ display: flex; gap: 8px; margin-bottom: 12px; }}
        .status-badge {{
            flex: 1;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }}
        .status-badge .count {{ font-size: 20px; font-weight: 700; }}
        .status-badge .label {{ font-size: 10px; color: #8b949e; text-transform: uppercase; }}
        .status-badge.red {{ background: rgba(248, 81, 73, 0.15); }}
        .status-badge.red .count {{ color: #f85149; }}
        .status-badge.orange {{ background: rgba(240, 136, 62, 0.15); }}
        .status-badge.orange .count {{ color: #f0883e; }}
        .status-badge.yellow {{ background: rgba(210, 153, 34, 0.15); }}
        .status-badge.yellow .count {{ color: #d29922; }}
        .status-badge.green {{ background: rgba(63, 185, 80, 0.15); }}
        .status-badge.green .count {{ color: #3fb950; }}
        
        .runway-section {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .runway-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        .runway-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .runway-table th {{
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid #30363d;
            color: #8b949e;
            font-weight: 500;
            font-size: 11px;
            text-transform: uppercase;
        }}
        .runway-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #21262d;
        }}
        .runway-table tr:hover {{ background: #161b22; }}
        .runway-days {{
            font-weight: 700;
            min-width: 60px;
        }}
        .runway-days.critical {{ color: #f85149; }}
        .runway-days.warning {{ color: #f0883e; }}
        .runway-days.ok {{ color: #d29922; }}
        .runway-days.good {{ color: #3fb950; }}
        .brand-tag {{
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .brand-tag.cardplug {{ background: rgba(163, 113, 247, 0.2); color: #a371f7; }}
        .brand-tag.blackowned {{ background: rgba(240, 136, 62, 0.2); color: #f0883e; }}
        .brand-tag.kinfolk {{ background: rgba(88, 166, 255, 0.2); color: #58a6ff; }}
        
        .updated {{
            text-align: center;
            color: #484f58;
            font-size: 11px;
            margin-top: 32px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">▲ Trifecta</div>
        <div class="nav-tabs">
            <a href="index.html" class="nav-tab">Overview</a>
            <a href="inventory.html" class="nav-tab active">Inventory</a>
            <a href="products.html" class="nav-tab">Products</a>
            <a href="profitability.html" class="nav-tab">Profitability</a>
        </div>
    </div>
    
    <div class="notice">
        <strong>ℹ️ FBA inventory only.</strong> AWD data not connected. Velocity is estimated — Sellerboard integration coming for accurate data.
    </div>
    
    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-value">{inventory.get('totals', {}).get('total_skus', 0)}</div>
            <div class="summary-label">Total SKUs</div>
        </div>
        <div class="summary-card">
            <div class="summary-value red">{inventory.get('totals', {}).get('out_of_stock', 0)}</div>
            <div class="summary-label">Out of Stock</div>
        </div>
        <div class="summary-card">
            <div class="summary-value orange">{inventory.get('totals', {}).get('low_stock', 0)}</div>
            <div class="summary-label">Low (&lt;50)</div>
        </div>
        <div class="summary-card">
            <div class="summary-value yellow">{inventory.get('totals', {}).get('medium_stock', 0)}</div>
            <div class="summary-label">Medium</div>
        </div>
        <div class="summary-card">
            <div class="summary-value green">{inventory.get('totals', {}).get('healthy', 0)}</div>
            <div class="summary-label">Healthy</div>
        </div>
    </div>
    
    <div class="section-title">📊 By Brand</div>
    <div class="brand-grid">
'''
    
    # Brand cards
    brand_order = ['cardplug', 'blackowned', 'kinfolk']
    for brand_key in brand_order:
        brand = inventory.get('brands', {}).get(brand_key, {})
        if not brand:
            continue
        html += f'''
        <div class="brand-card">
            <div class="brand-header">
                <div class="brand-name {brand_key}">{brand.get('name', brand_key)}</div>
                <div style="color:#8b949e;font-size:13px;">{brand.get('total_skus', 0)} SKUs</div>
            </div>
            <div class="status-row">
                <div class="status-badge red"><div class="count">{brand.get('out_of_stock', 0)}</div><div class="label">Out</div></div>
                <div class="status-badge orange"><div class="count">{brand.get('low_stock', 0)}</div><div class="label">Low</div></div>
                <div class="status-badge yellow"><div class="count">{brand.get('medium_stock', 0)}</div><div class="label">Med</div></div>
                <div class="status-badge green"><div class="count">{brand.get('healthy', 0)}</div><div class="label">Good</div></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:13px;color:#8b949e;">
                <span>FBA: <strong style="color:#e6edf3">{brand.get('total_fba_units', 0):,}</strong></span>
                <span>AWD: <strong style="color:#e6edf3">{brand.get('total_awd_units', 0):,}</strong></span>
            </div>
        </div>
'''
    
    # Separate urgent vs liquidation items
    in_stock_items = [i for i in all_items_by_runway if i.get('fba_qty', 0) > 0]
    
    # Urgent: runway < 90 days (need reorder attention)
    urgent_items = [i for i in in_stock_items if i.get('runway_days', 9999) < 90]
    urgent_items.sort(key=lambda x: x.get('runway_days', 9999))
    
    # Liquidation: runway > 180 days AND velocity < 1/day
    liquidation_items = [i for i in in_stock_items if i.get('runway_days', 9999) > 180 and i.get('daily_velocity', 0) < 1]
    liquidation_items.sort(key=lambda x: x.get('runway_days', 9999), reverse=True)
    
    html += '''
    </div>
    
    <div class="runway-section">
        <div class="runway-header">
            <div class="section-title" style="margin:0;">🚨 Reorder Watch (Under 90 Days Runway)</div>
        </div>
'''
    
    if urgent_items:
        html += '''
        <table class="runway-table">
            <thead>
                <tr>
                    <th>Days Left</th>
                    <th>Brand</th>
                    <th>Product</th>
                    <th>Stock</th>
                    <th>Velocity</th>
                </tr>
            </thead>
            <tbody>
'''
        for item in urgent_items[:20]:
            runway = item.get('runway_days', 9999)
            if runway < 30:
                runway_class = "critical"
            elif runway < 60:
                runway_class = "warning"
            else:
                runway_class = "ok"
            
            html += f'''
                <tr>
                    <td class="runway-days {runway_class}">{runway:.0f}</td>
                    <td><span class="brand-tag {item.get('brand_key', '')}">{item.get('brand', '')}</span></td>
                    <td>{item.get('name', '')[:45]}</td>
                    <td>{item.get('fba_qty', 0)}</td>
                    <td>{item.get('daily_velocity', 0):.1f}/day</td>
                </tr>
'''
        html += '''
            </tbody>
        </table>
'''
    else:
        html += '''
        <div style="text-align:center;padding:24px;color:#3fb950;">✓ All products have 90+ days of runway — no urgent reorders</div>
'''
    
    html += '''
    </div>
    
    <div class="runway-section" style="border-color: rgba(210, 153, 34, 0.3);">
        <div class="runway-header">
            <div class="section-title" style="margin:0;">🐌 Liquidation Candidates (Slow Sellers)</div>
        </div>
        <p style="color:#8b949e;font-size:13px;margin-bottom:16px;">Products selling &lt;1/day with 180+ days of stock sitting</p>
        <table class="runway-table">
            <thead>
                <tr>
                    <th>Days of Stock</th>
                    <th>Brand</th>
                    <th>Product</th>
                    <th>Stock</th>
                    <th>Velocity</th>
                </tr>
            </thead>
            <tbody>
'''
    
    for item in liquidation_items[:15]:
        runway = item.get('runway_days', 9999)
        runway_text = "∞" if runway >= 9999 else f"{runway:.0f}"
        
        html += f'''
                <tr>
                    <td class="runway-days" style="color:#d29922;">{runway_text}</td>
                    <td><span class="brand-tag {item.get('brand_key', '')}">{item.get('brand', '')}</span></td>
                    <td>{item.get('name', '')[:45]}</td>
                    <td>{item.get('fba_qty', 0)}</td>
                    <td style="color:#f85149;">{item.get('daily_velocity', 0):.1f}/day</td>
                </tr>
'''
    
    if not liquidation_items:
        html += '''
                <tr><td colspan="5" style="text-align:center;color:#8b949e;padding:20px;">No liquidation candidates</td></tr>
'''
    
    html += f'''
            </tbody>
        </table>
        <p style="color:#484f58;font-size:12px;margin-top:12px;">{len(liquidation_items)} total slow sellers identified</p>
    </div>
    
    <div class="updated">
        Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} CT
    </div>
</body>
</html>
'''
    
    # Save
    output_file = TRIFECTA_DIR / "inventory.html"
    output_file.write_text(html)
    print(f"✓ Inventory dashboard generated: {output_file}")

def main():
    print("Generating dashboards...")
    generate_inventory_html()
    print("Done!")

if __name__ == "__main__":
    main()
