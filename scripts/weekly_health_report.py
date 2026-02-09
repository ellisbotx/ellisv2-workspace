#!/usr/bin/env python3
"""
Weekly Business Health Report
Last 7 days vs prior 7 days across all 3 brands.
Posts to #reports every Monday 7 AM.
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

WORKSPACE = Path("/Users/ellisbot/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))
from discord_utils import post_report

SELLERBOARD_DIR = WORKSPACE / "data" / "sellerboard"
CSV_FILES = {
    "Black Owned": "blackowned_dashboard_by_product_90d.csv",
    "Card Plug": "cardplug_dashboard_by_product_90d.csv",
    "Kinfolk": "kinfolk_dashboard_by_product_90d.csv",
}

PROFIT_MARGIN_EST = 0.35  # estimated profit margin for rough calculation


def parse_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y")
    except ValueError:
        try:
            return datetime.strptime(date_str.strip(), "%m/%d/%Y")
        except ValueError:
            return None


def load_brand_data(csv_path):
    """Returns list of {date, sku, name, units, revenue, net_profit} dicts."""
    rows = []
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return rows

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = parse_date(row.get("Date", ""))
            if not date:
                continue
            
            organic_units = float(row.get("UnitsOrganic", 0) or 0)
            ppc_units = float(row.get("UnitsPPC", 0) or 0)
            organic_sales = float(row.get("SalesOrganic", 0) or 0)
            ppc_sales = float(row.get("SalesPPC", 0) or 0)
            net_profit = float(row.get("NetProfit", 0) or 0)

            rows.append({
                "date": date.date(),
                "sku": row.get("SKU", "").strip(),
                "name": row.get("Name", "").strip()[:60],
                "units": organic_units + ppc_units,
                "revenue": organic_sales + ppc_sales,
                "net_profit": net_profit,
            })
    return rows


def aggregate_period(rows, start_date, end_date):
    """Aggregate metrics for a date range."""
    filtered = [r for r in rows if start_date <= r["date"] <= end_date]
    
    total_revenue = sum(r["revenue"] for r in filtered)
    total_units = sum(r["units"] for r in filtered)
    total_profit = sum(r["net_profit"] for r in filtered)
    
    # SKU-level aggregation
    sku_data = defaultdict(lambda: {"units": 0, "revenue": 0, "net_profit": 0, "name": ""})
    for r in filtered:
        sku_data[r["sku"]]["units"] += r["units"]
        sku_data[r["sku"]]["revenue"] += r["revenue"]
        sku_data[r["sku"]]["net_profit"] += r["net_profit"]
        if r["name"]:
            sku_data[r["sku"]]["name"] = r["name"]

    return {
        "revenue": total_revenue,
        "units": total_units,
        "profit": total_profit,
        "sku_data": dict(sku_data),
    }


def pct_change(current, previous):
    if previous == 0:
        return 0 if current == 0 else 100
    return round(((current - previous) / abs(previous)) * 100, 1)


def arrow(pct):
    if pct > 0:
        return "📈"
    elif pct < 0:
        return "📉"
    return "➡️"


def main():
    today = datetime.now().date()
    # This week = last 7 days, prior week = 7 days before that
    this_week_end = today - timedelta(days=1)  # yesterday
    this_week_start = this_week_end - timedelta(days=6)
    prior_week_end = this_week_start - timedelta(days=1)
    prior_week_start = prior_week_end - timedelta(days=6)

    all_brand_data = {}
    total_this = {"revenue": 0, "units": 0, "profit": 0}
    total_prior = {"revenue": 0, "units": 0, "profit": 0}
    all_sku_this = {}

    for brand, csv_file in CSV_FILES.items():
        rows = load_brand_data(SELLERBOARD_DIR / csv_file)
        this_week = aggregate_period(rows, this_week_start, this_week_end)
        prior_week = aggregate_period(rows, prior_week_start, prior_week_end)

        all_brand_data[brand] = {"this": this_week, "prior": prior_week}
        
        for key in ["revenue", "units", "profit"]:
            total_this[key] += this_week[key]
            total_prior[key] += prior_week[key]

        # Collect SKU data with brand tag
        for sku, data in this_week["sku_data"].items():
            all_sku_this[f"{brand}|{sku}"] = data

    # Top/bottom SKUs by revenue
    sorted_skus = sorted(all_sku_this.items(), key=lambda x: -x[1]["revenue"])
    top_5 = sorted_skus[:5]
    bottom_5 = [s for s in sorted_skus if s[1]["units"] > 0][-5:]

    # Build message
    now = datetime.now().strftime("%b %d, %Y")
    rev_pct = pct_change(total_this["revenue"], total_prior["revenue"])
    unit_pct = pct_change(total_this["units"], total_prior["units"])
    profit_pct = pct_change(total_this["profit"], total_prior["profit"])

    msg = f"📊 **Weekly Business Health Report — {now}**\n"
    msg += f"Period: {this_week_start.strftime('%b %d')} – {this_week_end.strftime('%b %d')}\n\n"

    msg += "**Overall Performance (All Brands)**\n"
    msg += f"• Revenue: **${total_this['revenue']:,.2f}** {arrow(rev_pct)} {rev_pct:+.1f}% WoW\n"
    msg += f"• Units: **{int(total_this['units']):,}** {arrow(unit_pct)} {unit_pct:+.1f}% WoW\n"
    msg += f"• Est. Profit: **${total_this['profit']:,.2f}** {arrow(profit_pct)} {profit_pct:+.1f}% WoW\n\n"

    msg += "**By Brand**\n"
    for brand in CSV_FILES:
        bd = all_brand_data.get(brand, {})
        tw = bd.get("this", {"revenue": 0, "units": 0})
        pw = bd.get("prior", {"revenue": 0, "units": 0})
        r_pct = pct_change(tw["revenue"], pw["revenue"])
        msg += f"• **{brand}**: ${tw['revenue']:,.2f} rev / {int(tw['units']):,} units ({r_pct:+.1f}%)\n"

    msg += "\n**Top 5 SKUs (by revenue)**\n"
    for key, data in top_5:
        brand, sku = key.split("|", 1)
        name = data["name"] or sku
        msg += f"• {name[:40]} — ${data['revenue']:,.2f} ({int(data['units'])} units)\n"

    msg += "\n**Bottom 5 Active SKUs**\n"
    for key, data in bottom_5:
        brand, sku = key.split("|", 1)
        name = data["name"] or sku
        msg += f"• {name[:40]} — ${data['revenue']:,.2f} ({int(data['units'])} units)\n"

    if post_report(msg):
        print("Weekly health report posted to #reports")
    else:
        print("Failed to post")
        print(msg)


if __name__ == "__main__":
    main()
