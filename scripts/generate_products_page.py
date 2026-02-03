#!/usr/bin/env python3
"""
Generates the Products performance page for Trifecta dashboard.
Shows all SKUs ranked by revenue/velocity with performance indicators.
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

def generate_products_html():
    """Generate the products performance page"""
    
    inventory = load_json("inventory_dashboard.json")
    reorder = load_json("reorder_report.json")
    velocity = load_json("sku_velocity.json")

    # Build product list with all data
    products = []

    velocity_by_brand = (velocity.get("brands") or {})

    for brand_key, brand_data in reorder.get('brands', {}).items():
        brand_name = brand_data.get('brand', brand_key)

        brand_velocity = (velocity_by_brand.get(brand_key) or {}).get("skus") or {}

        for sku_data in brand_data.get('skus', []):
            sku = (sku_data.get('sku') or '').strip()
            if not sku:
                continue

            # Real 90-day revenue/units from Sellerboard (sku_velocity.json)
            vel_row = brand_velocity.get(sku) or {}
            units_90d = float(vel_row.get("units_90d") or 0)
            revenue_90d = float(vel_row.get("revenue_90d") or 0)

            # Derive 30d from 90d (Sellerboard export is 90-day window)
            units_30d = units_90d / 3
            revenue_30d = revenue_90d / 3

            # Prefer reorder_tracker's daily_velocity/runway, fall back to Sellerboard-derived
            daily_vel = sku_data.get('daily_velocity')
            if daily_vel is None:
                daily_vel = units_90d / 90 if units_90d else 0

            products.append({
                'sku': sku,
                'asin': sku_data.get('asin', ''),
                'name': sku_data.get('name', ''),
                'brand': brand_name,
                'brand_key': brand_key,
                'fba_qty': sku_data.get('fba_qty', 0),
                'daily_velocity': float(daily_vel),
                'units_30d': int(units_30d),
                'revenue_30d': round(revenue_30d, 2),
                'runway_days': sku_data.get('runway_days', 9999),
            })
    
    # Sort by revenue (highest first)
    products.sort(key=lambda x: x['revenue_30d'], reverse=True)
    
    # Categorize
    top_performers = [p for p in products if p['daily_velocity'] >= 2]  # 2+ per day
    solid_performers = [p for p in products if 0.5 <= p['daily_velocity'] < 2]
    slow_movers = [p for p in products if 0 < p['daily_velocity'] < 0.5]
    dead_stock = [p for p in products if p['daily_velocity'] == 0 and p['fba_qty'] > 0]
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Products | Trifecta</title>
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
        
        .summary-row {{
            display: flex;
            gap: 16px;
            margin-bottom: 32px;
        }}
        .summary-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px 24px;
            flex: 1;
        }}
        .summary-value {{ font-size: 28px; font-weight: 700; }}
        .summary-label {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
        .summary-value.green {{ color: #3fb950; }}
        .summary-value.blue {{ color: #58a6ff; }}
        .summary-value.yellow {{ color: #d29922; }}
        .summary-value.red {{ color: #f85149; }}
        
        .section {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .count-badge {{
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
        }}
        .count-badge.green {{ background: rgba(63, 185, 80, 0.2); color: #3fb950; }}
        .count-badge.blue {{ background: rgba(88, 166, 255, 0.2); color: #58a6ff; }}
        .count-badge.yellow {{ background: rgba(210, 153, 34, 0.2); color: #d29922; }}
        .count-badge.red {{ background: rgba(248, 81, 73, 0.2); color: #f85149; }}
        
        .product-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .product-table th {{
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid #30363d;
            color: #8b949e;
            font-weight: 500;
            font-size: 11px;
            text-transform: uppercase;
        }}
        .product-table td {{
            padding: 12px;
            border-bottom: 1px solid #21262d;
        }}
        .product-table tr:hover {{ background: rgba(88, 166, 255, 0.05); }}
        
        .brand-tag {{
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .brand-tag.cardplug {{ background: rgba(163, 113, 247, 0.2); color: #a371f7; }}
        .brand-tag.blackowned {{ background: rgba(240, 136, 62, 0.2); color: #f0883e; }}
        .brand-tag.kinfolk {{ background: rgba(88, 166, 255, 0.2); color: #58a6ff; }}
        
        .product-name {{
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .revenue {{ color: #3fb950; font-weight: 600; }}
        .velocity {{ color: #58a6ff; }}
        .stock {{ color: #8b949e; }}
        .runway {{ font-weight: 600; }}
        .runway.danger {{ color: #f85149; }}
        .runway.warning {{ color: #d29922; }}
        .runway.good {{ color: #3fb950; }}
        
        .updated {{
            text-align: center;
            color: #484f58;
            font-size: 11px;
            margin-top: 32px;
        }}
        
        .perf-bar {{
            width: 60px;
            height: 6px;
            background: #21262d;
            border-radius: 3px;
            overflow: hidden;
        }}
        .perf-bar-fill {{
            height: 100%;
            border-radius: 3px;
        }}
        .perf-bar-fill.high {{ background: #3fb950; }}
        .perf-bar-fill.med {{ background: #58a6ff; }}
        .perf-bar-fill.low {{ background: #d29922; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">▲ Trifecta</div>
        <div class="nav-tabs">
            <a href="index.html" class="nav-tab">Overview</a>
            <a href="inventory.html" class="nav-tab">Inventory</a>
            <a href="products.html" class="nav-tab active">Products</a>
            <a href="profitability.html" class="nav-tab">Profitability</a>
        </div>
    </div>
    
    <div class="summary-row">
        <div class="summary-card">
            <div class="summary-value green">{len(top_performers)}</div>
            <div class="summary-label">🔥 Top Performers (2+/day)</div>
        </div>
        <div class="summary-card">
            <div class="summary-value blue">{len(solid_performers)}</div>
            <div class="summary-label">✓ Solid (0.5-2/day)</div>
        </div>
        <div class="summary-card">
            <div class="summary-value yellow">{len(slow_movers)}</div>
            <div class="summary-label">⚠️ Slow (&lt;0.5/day)</div>
        </div>
        <div class="summary-card">
            <div class="summary-value red">{len(dead_stock)}</div>
            <div class="summary-label">💀 Dead Stock (0/day)</div>
        </div>
    </div>
'''
    
    # Top Performers Section
    if top_performers:
        max_rev = max(p['revenue_30d'] for p in top_performers) if top_performers else 1
        html += f'''
    <div class="section">
        <div class="section-header">
            <div class="section-title">🔥 Top Performers</div>
            <span class="count-badge green">{len(top_performers)} products</span>
        </div>
        <table class="product-table">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Rev (30d)</th>
                    <th>Velocity</th>
                    <th>Stock</th>
                    <th>Runway</th>
                    <th>Performance</th>
                </tr>
            </thead>
            <tbody>
'''
        for p in top_performers[:15]:
            runway_class = 'danger' if p['runway_days'] < 60 else 'warning' if p['runway_days'] < 90 else 'good'
            runway_text = f"{p['runway_days']:.0f}d" if p['runway_days'] < 9999 else "∞"
            perf_pct = min(100, (p['revenue_30d'] / max_rev) * 100) if max_rev > 0 else 0
            
            html += f'''
                <tr>
                    <td class="product-name" title="{p['name']}">{p['name'][:45]}</td>
                    <td><span class="brand-tag {p['brand_key']}">{p['brand']}</span></td>
                    <td class="revenue">${p['revenue_30d']:,.0f}</td>
                    <td class="velocity">{p['daily_velocity']:.1f}/day</td>
                    <td class="stock">{p['fba_qty']}</td>
                    <td class="runway {runway_class}">{runway_text}</td>
                    <td><div class="perf-bar"><div class="perf-bar-fill high" style="width:{perf_pct}%"></div></div></td>
                </tr>
'''
        html += '''
            </tbody>
        </table>
    </div>
'''
    
    # Solid Performers Section
    if solid_performers:
        html += f'''
    <div class="section">
        <div class="section-header">
            <div class="section-title">✓ Solid Performers</div>
            <span class="count-badge blue">{len(solid_performers)} products</span>
        </div>
        <table class="product-table">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Rev (30d)</th>
                    <th>Velocity</th>
                    <th>Stock</th>
                    <th>Runway</th>
                </tr>
            </thead>
            <tbody>
'''
        for p in solid_performers[:20]:
            runway_class = 'danger' if p['runway_days'] < 60 else 'warning' if p['runway_days'] < 90 else 'good'
            runway_text = f"{p['runway_days']:.0f}d" if p['runway_days'] < 9999 else "∞"
            
            html += f'''
                <tr>
                    <td class="product-name" title="{p['name']}">{p['name'][:45]}</td>
                    <td><span class="brand-tag {p['brand_key']}">{p['brand']}</span></td>
                    <td class="revenue">${p['revenue_30d']:,.0f}</td>
                    <td class="velocity">{p['daily_velocity']:.1f}/day</td>
                    <td class="stock">{p['fba_qty']}</td>
                    <td class="runway {runway_class}">{runway_text}</td>
                </tr>
'''
        if len(solid_performers) > 20:
            html += f'<tr><td colspan="6" style="color:#8b949e;text-align:center;">+ {len(solid_performers) - 20} more</td></tr>'
        html += '''
            </tbody>
        </table>
    </div>
'''
    
    # Slow Movers Section
    if slow_movers:
        html += f'''
    <div class="section" style="border-color: rgba(210, 153, 34, 0.3);">
        <div class="section-header">
            <div class="section-title">⚠️ Slow Movers</div>
            <span class="count-badge yellow">{len(slow_movers)} products</span>
        </div>
        <table class="product-table">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Rev (30d)</th>
                    <th>Velocity</th>
                    <th>Stock Sitting</th>
                </tr>
            </thead>
            <tbody>
'''
        for p in slow_movers[:15]:
            html += f'''
                <tr>
                    <td class="product-name" title="{p['name']}">{p['name'][:45]}</td>
                    <td><span class="brand-tag {p['brand_key']}">{p['brand']}</span></td>
                    <td class="revenue">${p['revenue_30d']:,.0f}</td>
                    <td class="velocity" style="color:#d29922;">{p['daily_velocity']:.2f}/day</td>
                    <td class="stock">{p['fba_qty']} units</td>
                </tr>
'''
        if len(slow_movers) > 15:
            html += f'<tr><td colspan="5" style="color:#8b949e;text-align:center;">+ {len(slow_movers) - 15} more</td></tr>'
        html += '''
            </tbody>
        </table>
    </div>
'''

    # Dead Stock Section
    if dead_stock:
        html += f'''
    <div class="section" style="border-color: rgba(248, 81, 73, 0.3);">
        <div class="section-header">
            <div class="section-title">💀 Dead Stock (No Sales)</div>
            <span class="count-badge red">{len(dead_stock)} products</span>
        </div>
        <p style="color:#8b949e;font-size:13px;margin-bottom:16px;">These products have inventory but zero velocity — consider liquidation</p>
        <table class="product-table">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Stock Sitting</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
'''
        for p in dead_stock[:20]:
            html += f'''
                <tr>
                    <td class="product-name" title="{p['name']}">{p['name'][:50]}</td>
                    <td><span class="brand-tag {p['brand_key']}">{p['brand']}</span></td>
                    <td style="color:#f85149;font-weight:600;">{p['fba_qty']} units</td>
                    <td style="color:#8b949e;">Liquidate / Promote</td>
                </tr>
'''
        if len(dead_stock) > 20:
            html += f'<tr><td colspan="4" style="color:#8b949e;text-align:center;">+ {len(dead_stock) - 20} more</td></tr>'
        html += '''
            </tbody>
        </table>
    </div>
'''
    
    html += f'''
    <div class="updated">
        Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} CT • Revenue/units from Sellerboard 90-day export
    </div>
</body>
</html>
'''
    
    # Save
    output_file = TRIFECTA_DIR / "products.html"
    output_file.write_text(html)
    print(f"✓ Products page generated: {output_file}")

if __name__ == "__main__":
    generate_products_html()
