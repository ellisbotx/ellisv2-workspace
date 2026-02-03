# Profitability Dashboard

## Overview
The Profitability Dashboard provides comprehensive financial metrics for all three Trifecta brands (Black Owned, Card Plug, Kinfolk) with both brand-level summaries and detailed SKU-level profitability analysis.

**URL:** `/Users/ellisbot/.openclaw/workspace/trifecta/profitability.html`

## Features

### Brand Summary Cards
Three side-by-side cards showing 90-day totals for each brand:
- **Sales** - Total revenue (organic + PPC)
- **Orders** - Total units sold
- **Refunds** - Number of refunded units
- **Adv. Cost** - Total advertising spend
- **Est. Payout** - Estimated Amazon payout
- **Net Profit** - Bottom line profitability
- **Margin %** - Profit margin percentage
- **ACOS** - Advertising Cost of Sale

**Color Coding:**
- 🟢 **Green border** = Profitable (Net Profit > $0)
- 🟡 **Yellow border** = Break-even (Net Profit -$100 to $0)
- 🔴 **Red border** = Losing money (Net Profit < -$100)

### SKU-Level Table
Sortable table showing all SKUs across all brands with:
- Brand name
- SKU
- Product name
- Units sold
- Revenue
- Ad spend
- Net profit
- Margin %
- ACOS

**Color Coding:**
- 🔴 **Red row** = Kill Zone (< $200/month profit) - Consider discontinuing
- 🟡 **Yellow row** = Warning (< 20% margin) - Needs optimization
- 🟢 **Green row** = Healthy (> 40% margin) - Good performer

**Sorting:** Click any column header to sort by that metric (ascending/descending toggle)

## Data Source
- **Location:** `/Users/ellisbot/.openclaw/workspace/data/sellerboard/`
- **Files:**
  - `blackowned_dashboard_by_product_90d.csv`
  - `cardplug_dashboard_by_product_90d.csv`
  - `kinfolk_dashboard_by_product_90d.csv`
- **Time Period:** Rolling 90 days (Nov 4, 2025 → Feb 2, 2026)
- **Marketplace:** Amazon.com only

## Generation Script
**Script:** `/Users/ellisbot/.openclaw/workspace/scripts/generate_profitability_page.py`

### What It Does:
1. Parses all three Sellerboard CSV files
2. Aggregates data by SKU (summing across all daily records)
3. Calculates brand-level totals
4. Generates static HTML with embedded data
5. Applies color coding based on profitability thresholds
6. Creates sortable table with JavaScript

### Manual Execution:
```bash
cd /Users/ellisbot/.openclaw/workspace/scripts
python3 generate_profitability_page.py
```

### Expected Output:
```
🔍 Generating Profitability Dashboard...
📊 Processing Black Owned...
   Revenue: $304,648.85
   Net Profit: $105,297.40
   Margin: 34.6%
📊 Processing Card Plug...
   Revenue: $263,686.41
   Net Profit: $120,859.26
   Margin: 45.8%
📊 Processing Kinfolk...
   Revenue: $225,458.55
   Net Profit: $75,191.71
   Margin: 33.4%

✅ Generated: /Users/ellisbot/.openclaw/workspace/trifecta/profitability.html
📦 Total SKUs: 174
```

## Automation

### Daily Workflow
The profitability page is automatically regenerated as part of the daily Sellerboard processing workflow.

**Script:** `/Users/ellisbot/.openclaw/workspace/scripts/sellerboard_daily.sh`

**Execution:** Integrated into the 2 AM CST daily cron job

**Workflow Steps:**
1. Verify CSV files exist and are up-to-date
2. Process CSVs into `sku_velocity.json`
3. Generate profitability dashboard HTML

### Manual Execution:
```bash
bash /Users/ellisbot/.openclaw/workspace/scripts/sellerboard_daily.sh
```

## Navigation
The Profitability page has been added to the navigation bar on all Trifecta dashboard pages:
- ✅ `index.html` (Overview)
- ✅ `inventory.html` (Inventory)
- ✅ `products.html` (Products)
- ✅ `profitability.html` (Profitability) - **NEW**

## Key Metrics Explained

### Kill Threshold ($200/month)
SKUs with monthly net profit below $200 appear in red. This is based on 90-day data divided by 3.

**Rationale:** Products not generating at least $200/month likely aren't worth the inventory investment and operational overhead.

**Action:** Review red SKUs for potential discontinuation or aggressive optimization.

### Margin Thresholds
- **< 20%** (Yellow) = Low margin, vulnerable to cost increases
- **20-40%** (Normal) = Standard performance
- **> 40%** (Green) = Strong margin, good pricing power

### ACOS (Advertising Cost of Sale)
Percentage of sales spent on advertising. Lower is generally better, but context matters:
- **< 20%** = Efficient advertising
- **20-30%** = Acceptable for competitive markets
- **> 30%** = May need optimization

## Revenue Validation
Based on 90-day data (Nov 4, 2025 → Feb 2, 2026):

| Brand | 90-Day Revenue | Monthly Avg |
|-------|---------------|-------------|
| Black Owned | $304,648.85 | ~$101,550 |
| Card Plug | $263,686.41 | ~$87,895 |
| Kinfolk | $225,458.55 | ~$75,153 |
| **Total** | **$793,793.81** | **$264,598** |

## Troubleshooting

### Missing Data
If brands show $0.00 revenue:
1. Check if CSV files exist in `/Users/ellisbot/.openclaw/workspace/data/sellerboard/`
2. Verify CSV files contain data (should be ~12,000-13,000 rows each)
3. Check file modification dates (should be recent)
4. Re-run the generation script manually

### Incorrect Calculations
The script uses these formulas:
- **Total Sales** = SalesOrganic + SalesPPC
- **Total Units** = UnitsOrganic + UnitsPPC
- **Ad Spend** = abs(SponsoredProducts) (made positive)
- **Margin %** = (NetProfit / Sales) * 100
- **ACOS** = (AdSpend / Sales) * 100

All monetary values are summed across all daily records for each SKU, then aggregated by brand.

### CSV Format Changes
If Sellerboard changes their CSV format, update the column names in `generate_profitability_page.py`:
- Look for the `csv.DictReader()` section
- Update column name references (e.g., 'SalesOrganic', 'NetProfit', etc.)

## File Locations

### Generated Files
- **HTML Output:** `/Users/ellisbot/.openclaw/workspace/trifecta/profitability.html`

### Source Files
- **Generator Script:** `/Users/ellisbot/.openclaw/workspace/scripts/generate_profitability_page.py`
- **Daily Workflow:** `/Users/ellisbot/.openclaw/workspace/scripts/sellerboard_daily.sh`
- **Data Files:** `/Users/ellisbot/.openclaw/workspace/data/sellerboard/*.csv`

### Modified Files (Navigation Updates)
- `/Users/ellisbot/.openclaw/workspace/trifecta/index.html`
- `/Users/ellisbot/.openclaw/workspace/trifecta/inventory.html`
- `/Users/ellisbot/.openclaw/workspace/trifecta/products.html`

## Design Notes

### Styling
- Matches existing Trifecta dashboard dark theme
- Blue/purple/pink gradient for logo
- Dark backgrounds (#0d1117, #161b22)
- Border colors for visual hierarchy
- Mobile-responsive grid layouts

### Color Palette
- **Background:** #0d1117 (body), #161b22 (cards)
- **Borders:** #30363d (neutral), #3fb950 (success), #d29922 (warning), #f85149 (danger)
- **Text:** #e6edf3 (primary), #8b949e (muted)
- **Accent:** #58a6ff (blue), #a371f7 (purple), #f778ba (pink)

### Performance
- Static HTML generation (no database queries)
- All data embedded at generation time
- Client-side sorting via JavaScript
- ~156KB file size (includes all SKU data)

## Future Enhancements

Potential improvements:
- [ ] Add date range filter (30/60/90 days)
- [ ] Show trend arrows (vs previous period)
- [ ] Add SKU search/filter functionality
- [ ] Export to CSV/Excel
- [ ] Add category/product type grouping
- [ ] Show top/bottom performers
- [ ] Add profit per order metric
- [ ] Include inventory value correlation
- [ ] Add break-even analysis

## Support
For issues or questions:
1. Check logs in `/Users/ellisbot/.openclaw/workspace/data/sellerboard/daily_processing.log`
2. Review this README and other documentation in `/Users/ellisbot/.openclaw/workspace/scripts/`
3. Test generation manually to isolate issues
