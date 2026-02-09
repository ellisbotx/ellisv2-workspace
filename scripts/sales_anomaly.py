#!/usr/bin/env python3
"""
Daily Sales Anomaly Detection
Compares 7-day avg velocity to 30-day avg. Flags drops >40% or spikes >50%.
Posts to #alerts if anomalies found, #reports if all normal.
"""

import csv
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

WORKSPACE = Path("/Users/ellisbot/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))
from discord_utils import post_alert, post_report

SELLERBOARD_DIR = WORKSPACE / "data" / "sellerboard"
CSV_FILES = {
    "Black Owned": "blackowned_dashboard_by_product_90d.csv",
    "Card Plug": "cardplug_dashboard_by_product_90d.csv",
    "Kinfolk": "kinfolk_dashboard_by_product_90d.csv",
}

DROP_THRESHOLD = 0.40   # flag if dropped >40%
SPIKE_THRESHOLD = 0.50  # flag if spiked >50%


def load_liquidation_asins():
    path = WORKSPACE / "data" / "liquidation_asins.txt"
    asins = set()
    if not path.exists():
        return asins
    for line in path.read_text().splitlines():
        parts = line.strip().split(" - ")
        if len(parts) >= 2:
            asin = parts[-1].strip()
            if asin.startswith("B0"):
                asins.add(asin)
    return asins


def parse_date(date_str):
    """Parse date from sellerboard CSV (DD/MM/YYYY format)."""
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y")
    except ValueError:
        try:
            return datetime.strptime(date_str.strip(), "%m/%d/%Y")
        except ValueError:
            return None


def load_daily_units(csv_path):
    """Load daily unit sales per SKU from sellerboard CSV.
    Returns: {sku: {date: units}}
    """
    sku_daily = defaultdict(lambda: defaultdict(int))
    sku_names = {}
    sku_asins = {}

    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return sku_daily, sku_names, sku_asins

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = parse_date(row.get("Date", ""))
            if not date:
                continue
            sku = row.get("SKU", "").strip()
            asin = row.get("ASIN", "").strip()
            name = row.get("Name", "").strip()
            
            organic = float(row.get("UnitsOrganic", 0) or 0)
            ppc = float(row.get("UnitsPPC", 0) or 0)
            total_units = organic + ppc

            sku_daily[sku][date.date()] += total_units
            if name:
                sku_names[sku] = name[:60]  # truncate long names
            if asin:
                sku_asins[sku] = asin

    return sku_daily, sku_names, sku_asins


def detect_anomalies():
    liquidation_asins = load_liquidation_asins()
    today = datetime.now().date()
    
    # Use the most recent date in data as reference
    drops = []
    spikes = []

    for brand, csv_file in CSV_FILES.items():
        csv_path = SELLERBOARD_DIR / csv_file
        sku_daily, sku_names, sku_asins = load_daily_units(csv_path)

        for sku, daily_data in sku_daily.items():
            asin = sku_asins.get(sku, "")
            if asin in liquidation_asins:
                continue

            # Get all dates sorted
            dates = sorted(daily_data.keys())
            if not dates:
                continue

            latest_date = dates[-1]
            
            # Calculate 7-day and 30-day averages ending at latest_date
            last_7 = [daily_data.get(latest_date - timedelta(days=i), 0) for i in range(7)]
            last_30 = [daily_data.get(latest_date - timedelta(days=i), 0) for i in range(30)]

            avg_7 = sum(last_7) / 7 if last_7 else 0
            avg_30 = sum(last_30) / 30 if last_30 else 0

            if avg_30 <= 0:
                continue  # skip dead SKUs

            pct_change = (avg_7 - avg_30) / avg_30
            name = sku_names.get(sku, sku)

            entry = {
                "sku": sku,
                "asin": asin,
                "name": name,
                "brand": brand,
                "avg_7": round(avg_7, 2),
                "avg_30": round(avg_30, 2),
                "pct_change": round(pct_change * 100, 1),
            }

            if pct_change < -DROP_THRESHOLD:
                drops.append(entry)
            elif pct_change > SPIKE_THRESHOLD:
                spikes.append(entry)

    return drops, spikes


def main():
    now = datetime.now().strftime("%b %d, %Y")
    drops, spikes = detect_anomalies()

    total_anomalies = len(drops) + len(spikes)

    if total_anomalies == 0:
        msg = f"📊 **Sales Anomaly Check — {now}**\n\n✅ No significant velocity changes detected. All SKUs within normal range."
        post_report(msg, silent=True)
        print("All normal - posted to #reports")
        return

    msg = f"⚠️ **Sales Anomaly Alert — {now}**\n{total_anomalies} SKUs with unusual velocity changes\n"

    if drops:
        drops.sort(key=lambda x: x["pct_change"])
        msg += f"\n📉 **Velocity Drops (>{int(DROP_THRESHOLD*100)}% decline)** — {len(drops)} SKUs\n"
        for d in drops[:10]:
            msg += (
                f"• **{d['name']}** ({d['brand']})\n"
                f"  7-day avg: {d['avg_7']}/day → 30-day avg: {d['avg_30']}/day "
                f"(**{d['pct_change']}%**)\n"
            )
        if len(drops) > 10:
            msg += f"  ...and {len(drops) - 10} more\n"

    if spikes:
        spikes.sort(key=lambda x: -x["pct_change"])
        msg += f"\n📈 **Velocity Spikes (>{int(SPIKE_THRESHOLD*100)}% increase)** — {len(spikes)} SKUs\n"
        for s in spikes[:10]:
            msg += (
                f"• **{s['name']}** ({s['brand']})\n"
                f"  7-day avg: {s['avg_7']}/day → 30-day avg: {s['avg_30']}/day "
                f"(**+{s['pct_change']}%**)\n"
            )
        if len(spikes) > 10:
            msg += f"  ...and {len(spikes) - 10} more\n"

    if post_alert(msg):
        print(f"Posted anomaly alert: {len(drops)} drops, {len(spikes)} spikes")
    else:
        print("Failed to post to Discord")
        print(msg)


if __name__ == "__main__":
    main()
