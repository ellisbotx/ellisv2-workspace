#!/usr/bin/env python3
"""
Generate Profitability Dashboard for Trifecta
Parses Sellerboard CSVs and creates profitability.html with brand and SKU-level metrics
"""

import csv
import html as html_lib
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")
TRIFECTA_DIR = Path("/Users/ellisbot/.openclaw/workspace/trifecta")

# Brand mapping - map CSV filenames to brand names
BRAND_FILES = {
    "Black Owned": "blackowned_dashboard_by_product_90d.csv",
    "Card Plug": "cardplug_dashboard_by_product_90d.csv",
    "Kinfolk": "kinfolk_dashboard_by_product_90d.csv"
}

def parse_float(value):
    """Parse float value, handling empty strings and quotes"""
    if not value or value == '':
        return 0.0
    try:
        # Remove quotes and convert
        return float(str(value).strip('"'))
    except (ValueError, TypeError):
        return 0.0

def parse_int(value):
    """Parse integer value"""
    if not value or value == '':
        return 0
    try:
        return int(float(str(value).strip('"')))
    except (ValueError, TypeError):
        return 0

def _parse_row_date(date_str):
    """Parse Sellerboard 'Date' column to a date object.

    Sellerboard exports are commonly DD/MM/YYYY but sometimes MM/DD/YYYY.
    Returns None if unparseable/blank.
    """
    s = (date_str or '').strip()
    if not s:
        return None

    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def load_sellerboard_csv(
    filepath,
    start_date=None,
    end_date=None,
    marketplace_filter="Amazon.com",
    period_days=90,
):
    """Load and parse a Sellerboard CSV file with date + marketplace filters.

    Filters mirror scripts/sellerboard_export.py:
      - Date range defaults to last `period_days` ending today
      - Marketplace defaults to Amazon.com (US)

    IMPORTANT: revenue is SalesOrganic + SalesPPC ONLY (do not triple-count ad sales).
    """
    data = []

    # Resolve date range
    today = datetime.now().date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else today
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else (end_dt - timedelta(days=period_days))

    with open(filepath, 'r', encoding='utf-8-sig', errors='replace', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            # Filter by date range
            row_date = _parse_row_date(row.get('Date'))
            if row_date is not None and (row_date < start_dt or row_date > end_dt):
                continue

            # Filter by marketplace (US only by default)
            marketplace = (row.get('Marketplace') or '').strip()
            if marketplace_filter and marketplace != marketplace_filter:
                continue

            # Parse numeric fields
            # NOTE: SalesPPC is already aggregated (SponsoredProducts+SponsoredDisplay).
            # Adding those separately would triple-count ad sales.
            sales_organic = parse_float(row.get('SalesOrganic', 0))
            sales_ppc = parse_float(row.get('SalesPPC', 0))
            total_sales = sales_organic + sales_ppc

            units_organic = parse_int(row.get('UnitsOrganic', 0))
            units_ppc = parse_int(row.get('UnitsPPC', 0))
            total_units = units_organic + units_ppc

            refunds = parse_int(row.get('Refunds', 0))
            ad_spend = abs(parse_float(row.get('SponsoredProducts', 0)))  # Make positive
            amazon_fees = abs(parse_float(row.get('AmazonFees', 0)))  # Make positive
            net_profit = parse_float(row.get('NetProfit', 0))
            margin = parse_float(row.get('Margin', 0))
            est_payout = parse_float(row.get('EstimatedPayout', 0))

            data.append({
                'sku': row.get('SKU', ''),
                'name': row.get('Name', ''),
                'sales': total_sales,
                'units': total_units,
                'refunds': refunds,
                'ad_spend': ad_spend,
                'amazon_fees': amazon_fees,
                'net_profit': net_profit,
                'margin': margin,
                'est_payout': est_payout
            })

    return data

def aggregate_by_sku(data):
    """Aggregate data by SKU"""
    sku_data = defaultdict(lambda: {
        'name': '',
        'sales': 0,
        'units': 0,
        'refunds': 0,
        'ad_spend': 0,
        'amazon_fees': 0,
        'net_profit': 0,
        'est_payout': 0
    })
    
    for row in data:
        sku = row['sku']
        sku_data[sku]['name'] = row['name']  # Take last name
        sku_data[sku]['sales'] += row['sales']
        sku_data[sku]['units'] += row['units']
        sku_data[sku]['refunds'] += row['refunds']
        sku_data[sku]['ad_spend'] += row['ad_spend']
        sku_data[sku]['amazon_fees'] += row['amazon_fees']
        sku_data[sku]['net_profit'] += row['net_profit']
        sku_data[sku]['est_payout'] += row['est_payout']
    
    # Calculate margin for each SKU
    for sku in sku_data:
        if sku_data[sku]['sales'] > 0:
            sku_data[sku]['margin'] = (sku_data[sku]['net_profit'] / sku_data[sku]['sales']) * 100
        else:
            sku_data[sku]['margin'] = 0
    
    return sku_data

def calculate_brand_totals(sku_data):
    """Calculate brand-level totals"""
    totals = {
        'sales': 0,
        'units': 0,
        'refunds': 0,
        'ad_spend': 0,
        'est_payout': 0,
        'net_profit': 0,
        'margin': 0
    }
    
    for sku, data in sku_data.items():
        totals['sales'] += data['sales']
        totals['units'] += data['units']
        totals['refunds'] += data['refunds']
        totals['ad_spend'] += data['ad_spend']
        totals['est_payout'] += data['est_payout']
        totals['net_profit'] += data['net_profit']
    
    # Calculate overall margin
    if totals['sales'] > 0:
        totals['margin'] = (totals['net_profit'] / totals['sales']) * 100
    
    return totals

def get_brand_color_class(net_profit):
    """Determine color class for brand card based on profitability"""
    if net_profit > 0:
        return 'profitable'
    elif net_profit >= -100:
        return 'breakeven'
    else:
        return 'losing'

def get_sku_row_class(net_profit, margin, monthly_profit):
    """Determine color class for SKU row based on thresholds"""
    # Calculate monthly profit (90-day data / 3)
    if monthly_profit < 200:
        return 'kill-zone'
    elif margin < 20:
        return 'warning'
    elif margin > 40:
        return 'healthy'
    return ''

def format_currency(value):
    """Format value as currency"""
    if value >= 0:
        return f"${value:,.2f}"
    else:
        return f"-${abs(value):,.2f}"

def format_percent(value):
    """Format value as percentage"""
    return f"{value:.1f}%"

def truncate_words(text, num_words=3, suffix="..."):
    """Return the first `num_words` words of `text` (whitespace-split).

    If the text has more than `num_words` words, append `suffix`.
    """
    if not text:
        return ""

    words = str(text).split()
    if len(words) <= num_words:
        return " ".join(words)

    return " ".join(words[:num_words]) + suffix

def generate_html(brands_data, all_skus, brand_order=None, missing_brands=None):
    """Generate the profitability HTML page.

    Args:
        brands_data: dict of brand_name -> totals
        all_skus: list of (brand_name, sku, data)
        brand_order: preferred ordering for display
        missing_brands: list of brand names that were expected but missing
    """

    brand_order = brand_order or list(brands_data.keys())
    missing_brands = missing_brands or []

    # Generate brand cards HTML (only for available brands)
    brand_cards_html = ""
    for brand_name in brand_order:
        totals = brands_data.get(brand_name)
        if not totals:
            continue
        color_class = get_brand_color_class(totals['net_profit'])
        acos = (totals['ad_spend'] / totals['sales'] * 100) if totals['sales'] > 0 else 0

        brand_cards_html += f'''
        <div class="brand-card {color_class}">
            <div class="brand-name">{brand_name}</div>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Sales</div>
                    <div class="metric-value">{format_currency(totals['sales'])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Orders</div>
                    <div class="metric-value">{totals['units']:,}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Refunds</div>
                    <div class="metric-value">{totals['refunds']:,}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Adv. Cost</div>
                    <div class="metric-value">{format_currency(totals['ad_spend'])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Est. Payout</div>
                    <div class="metric-value">{format_currency(totals['est_payout'])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Net Profit</div>
                    <div class="metric-value profit">{format_currency(totals['net_profit'])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Margin</div>
                    <div class="metric-value">{format_percent(totals['margin'])}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">ACOS</div>
                    <div class="metric-value">{format_percent(acos)}</div>
                </div>
            </div>
        </div>
        '''
    
    # Generate SKU table rows
    sku_rows_html = ""
    for brand_name, sku, data in all_skus:
        monthly_profit = data['net_profit'] / 3  # 90-day data divided by 3
        row_class = get_sku_row_class(data['net_profit'], data['margin'], monthly_profit)
        acos = (data['ad_spend'] / data['sales'] * 100) if data['sales'] > 0 else 0

        # Shorten display name but keep full name for sorting + tooltip
        full_name = data.get('name', '') or ''
        display_name = truncate_words(full_name, 3)

        brand_name_esc = html_lib.escape(str(brand_name))
        sku_esc = html_lib.escape(str(sku))
        full_name_esc = html_lib.escape(str(full_name))
        display_name_esc = html_lib.escape(str(display_name))

        sku_rows_html += f'''
        <tr class="{row_class}">
            <td data-sort="{brand_name_esc}">{brand_name_esc}</td>
            <td data-sort="{sku_esc}">{sku_esc}</td>
            <td data-sort="{full_name_esc}" title="{full_name_esc}">{display_name_esc}</td>
            <td data-sort="{data['units']}">{data['units']:,}</td>
            <td data-sort="{data['sales']}">{format_currency(data['sales'])}</td>
            <td data-sort="{data['ad_spend']}">{format_currency(data['ad_spend'])}</td>
            <td data-sort="{data['net_profit']}">{format_currency(data['net_profit'])}</td>
            <td data-sort="{data['margin']}">{format_percent(data['margin'])}</td>
            <td data-sort="{acos}">{format_percent(acos)}</td>
        </tr>
        '''

    warning_html = ""
    if missing_brands:
        missing_list = ", ".join(missing_brands)
        warning_html = f'''<div class="warning-banner"><strong>⚠ Missing Sellerboard exports:</strong> {missing_list}. Showing available brands only.</div>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profitability | Trifecta</title>
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
        
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #e6edf3;
        }}
        
        /* Brand Cards */
        .brand-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}

        .warning-banner {{
            background: rgba(210, 153, 34, 0.12);
            border: 1px solid rgba(210, 153, 34, 0.35);
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 20px;
            color: #d29922;
            font-size: 13px;
        }}
        .warning-banner strong {{ color: #e6edf3; }}
        
        .brand-card {{
            background: #161b22;
            border: 2px solid #30363d;
            border-radius: 12px;
            padding: 24px;
        }}
        
        .brand-card.profitable {{ border-color: #3fb950; }}
        .brand-card.breakeven {{ border-color: #d29922; }}
        .brand-card.losing {{ border-color: #f85149; }}
        
        .brand-name {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
        
        .metric {{
            text-align: center;
        }}
        
        .metric-label {{
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        
        .metric-value {{
            font-size: 16px;
            font-weight: 600;
            color: #e6edf3;
        }}
        
        .metric-value.profit {{
            font-size: 20px;
            font-weight: 700;
        }}
        
        /* SKU Table */
        .table-container {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            overflow: hidden;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #21262d;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        th {{
            padding: 12px 16px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            color: #58a6ff;
        }}
        
        th.sortable::after {{
            content: ' ↕';
            opacity: 0.3;
        }}
        
        th.sort-asc::after {{
            content: ' ↑';
            opacity: 1;
            color: #58a6ff;
        }}
        
        th.sort-desc::after {{
            content: ' ↓';
            opacity: 1;
            color: #58a6ff;
        }}
        
        td {{
            padding: 12px 16px;
            font-size: 13px;
            border-top: 1px solid #21262d;
        }}
        
        tr.kill-zone {{
            background: rgba(248, 81, 73, 0.1);
        }}
        
        tr.warning {{
            background: rgba(210, 153, 34, 0.1);
        }}
        
        tr.healthy {{
            background: rgba(63, 185, 80, 0.1);
        }}
        
        tbody tr:hover {{
            background: rgba(56, 139, 253, 0.1);
        }}
        
        /* Mobile Responsive */
        @media (max-width: 1024px) {{
            .brand-cards {{
                grid-template-columns: 1fr;
            }}
            
            .metrics-grid {{
                grid-template-columns: repeat(4, 1fr);
            }}
            
            table {{
                font-size: 12px;
            }}
            
            th, td {{
                padding: 8px 12px;
            }}
        }}
        
        .legend {{
            display: flex;
            gap: 24px;
            margin-bottom: 16px;
            font-size: 12px;
            color: #8b949e;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }}
        
        .legend-color.red {{ background: rgba(248, 81, 73, 0.3); }}
        .legend-color.yellow {{ background: rgba(210, 153, 34, 0.3); }}
        .legend-color.green {{ background: rgba(63, 185, 80, 0.3); }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Trifecta</div>
        <div class="nav-tabs">
            <a href="index.html" class="nav-tab">Overview</a>
            <a href="inventory.html" class="nav-tab">Inventory</a>
            <a href="products.html" class="nav-tab">Products</a>
            <a href="profitability.html" class="nav-tab active">Profitability</a>
        </div>
    </div>

    {warning_html}

    <div class="section-title">Brand Performance (90 Days)</div>
    <div class="brand-cards">
        {brand_cards_html}
    </div>
    
    <div class="section-title">SKU-Level Profitability</div>
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color red"></div>
            <span>Kill Zone (&lt;$200/mo)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color yellow"></div>
            <span>Warning (&lt;20% margin)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color green"></div>
            <span>Healthy (&gt;40% margin)</span>
        </div>
    </div>
    
    <div class="table-container">
        <table id="profitabilityTable">
            <thead>
                <tr>
                    <th class="sortable" onclick="sortTable(0)">Brand</th>
                    <th class="sortable" onclick="sortTable(1)">SKU</th>
                    <th class="sortable" onclick="sortTable(2)">Product Name</th>
                    <th class="sortable" onclick="sortTable(3)">Units</th>
                    <th class="sortable" onclick="sortTable(4)">Revenue</th>
                    <th class="sortable" onclick="sortTable(5)">Ad Spend</th>
                    <th class="sortable" onclick="sortTable(6)">Net Profit</th>
                    <th class="sortable" onclick="sortTable(7)">Margin %</th>
                    <th class="sortable" onclick="sortTable(8)">ACOS</th>
                </tr>
            </thead>
            <tbody>
                {sku_rows_html}
            </tbody>
        </table>
    </div>
    
    <script>
        let currentSort = {{
            column: -1,
            ascending: true
        }};
        
        function sortTable(columnIndex) {{
            const table = document.getElementById('profitabilityTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle sort direction if same column
            if (currentSort.column === columnIndex) {{
                currentSort.ascending = !currentSort.ascending;
            }} else {{
                currentSort.column = columnIndex;
                currentSort.ascending = false; // Default to descending for numbers
            }}
            
            // Sort rows
            rows.sort((a, b) => {{
                const aCell = a.cells[columnIndex];
                const bCell = b.cells[columnIndex];
                
                const aValue = aCell.getAttribute('data-sort') || aCell.textContent;
                const bValue = bCell.getAttribute('data-sort') || bCell.textContent;
                
                // Try numeric sort first
                const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return currentSort.ascending ? aNum - bNum : bNum - aNum;
                }}
                
                // Fall back to string sort
                return currentSort.ascending 
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            }});
            
            // Clear existing rows and add sorted
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
            
            // Update header indicators
            table.querySelectorAll('th').forEach((th, idx) => {{
                th.classList.remove('sort-asc', 'sort-desc');
                if (idx === columnIndex) {{
                    th.classList.add(currentSort.ascending ? 'sort-asc' : 'sort-desc');
                }}
            }});
        }}
        
        // Default sort by Net Profit descending
        sortTable(6);
    </script>
</body>
</html>'''
    
    return html

def main():
    print("🔍 Generating Profitability Dashboard...")
    
    brands_data = {}
    all_skus = []
    missing_brands = []
    expected_order = ["Black Owned", "Card Plug", "Kinfolk"]

    # Load and process each brand
    for brand_name, filename in BRAND_FILES.items():
        filepath = DATA_DIR / filename
        
        if not filepath.exists():
            print(f"⚠️  Warning: {filename} not found, skipping {brand_name}")
            missing_brands.append(brand_name)
            continue
        
        print(f"📊 Processing {brand_name}...")
        
        # Load CSV data (filter to last 90 days + Amazon.com US only)
        end_dt = datetime.now().date()
        start_dt = end_dt - timedelta(days=90)
        raw_data = load_sellerboard_csv(
            filepath,
            start_date=start_dt.isoformat(),
            end_date=end_dt.isoformat(),
            marketplace_filter="Amazon.com",
            period_days=90,
        )
        
        # Aggregate by SKU
        sku_data = aggregate_by_sku(raw_data)
        
        # Calculate brand totals
        totals = calculate_brand_totals(sku_data)
        brands_data[brand_name] = totals
        
        print(f"   Revenue: {format_currency(totals['sales'])}")
        print(f"   Net Profit: {format_currency(totals['net_profit'])}")
        print(f"   Margin: {format_percent(totals['margin'])}")
        
        # Add to all_skus list
        for sku, data in sku_data.items():
            all_skus.append((brand_name, sku, data))
    
    # Sort all SKUs by net profit descending
    all_skus.sort(key=lambda x: x[2]['net_profit'], reverse=True)
    
    # Generate HTML
    html = generate_html(brands_data, all_skus, brand_order=expected_order, missing_brands=missing_brands)
    
    # Write to file
    output_path = TRIFECTA_DIR / "profitability.html"
    output_path.write_text(html)
    
    print(f"\n✅ Generated: {output_path}")
    print(f"📦 Total SKUs: {len(all_skus)}")
    
    # Print validation totals
    print("\n📊 Revenue Validation:")
    for brand_name in ["Black Owned", "Card Plug", "Kinfolk"]:
        if brand_name in brands_data:
            print(f"   {brand_name}: {format_currency(brands_data[brand_name]['sales'])}")

if __name__ == "__main__":
    main()
