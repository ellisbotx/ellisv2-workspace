#!/usr/bin/env python3
"""Sellerboard export processing helper.

We currently rely on Sellerboard UI exports (no API).

Important: Sellerboard's Products page CSV export is *not* sales/velocity.
For velocity we use Reports -> "Dashboard by product" export which includes
per-day sales/units broken down by channel.

This script processes downloaded CSVs into a single JSON file:
  /Users/ellisbot/.openclaw/workspace/data/sku_velocity.json

Expected input files (preferred):
  data/sellerboard/{brand}_dashboard_by_product_90d.csv
Where brand is one of: blackowned, cardplug, kinfolk

Legacy inputs (still supported):
  data/sellerboard/{brand}_sales_90d.csv
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

DATA_DIR = Path("/Users/ellisbot/.openclaw/workspace/data/sellerboard")
DATA_DIR.mkdir(parents=True, exist_ok=True)

BRANDS = ("blackowned", "cardplug", "kinfolk")

# Brand mapping in Sellerboard dropdown (human/UI names)
BRAND_MAPPING = {
    "Summary Dashboard": "blackowned",  # sellerboard label for srgrier45 (Black Owned)
    "CardPlug": "cardplug",
    "Kinfolk": "kinfolk",
}


def get_export_instructions() -> str:
    return """
SELLERBOARD EXPORT (VELOCITY) INSTRUCTIONS
=========================================

Goal: export per-product sales & units for last 90 days for each brand.

For each brand (Summary Dashboard / CardPlug / Kinfolk):
1) Go to Reports: https://app.sellerboard.com/en/export
2) Click: "Dashboard by product"
3) Set date range:
   - From: 90 days ago
   - To: today
4) Select file format: .CSV
5) Click Download
6) Save/move file to:
   data/sellerboard/{brand}_dashboard_by_product_90d.csv

Then run:
  python3 scripts/sellerboard_export.py --process

Notes:
- Products -> Export -> CSV is NOT a sales report (it lacks units/revenue).
- The Reports -> Dashboard by product export includes daily Sales/Units columns.
"""


def _to_float(value: str) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    # remove currency symbols and thousands separators
    s = s.replace("$", "").replace(",", "")
    # some exports can include spaces
    s = s.replace(" ", "")
    try:
        return float(s)
    except Exception:
        return 0.0


def _to_int(value: str) -> int:
    if value is None:
        return 0
    s = str(value).strip()
    if not s:
        return 0
    s = s.replace(",", "").replace(" ", "")
    try:
        return int(float(s))
    except Exception:
        return 0


@dataclass
class SkuAgg:
    units: int = 0
    revenue: float = 0.0


def process_dashboard_by_product_csv(
    filepath: Path,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    marketplace_filter: str = "Amazon.com",
) -> Dict[str, SkuAgg]:
    """Aggregate per-SKU totals from Sellerboard Reports -> Dashboard by product export.
    
    Args:
        filepath: Path to CSV file
        start_date: Filter start date (YYYY-MM-DD format)
        end_date: Filter end date (YYYY-MM-DD format)
        marketplace_filter: Only include this marketplace (default: Amazon.com = US only)
    """
    sku_data: Dict[str, SkuAgg] = {}

    if not filepath.exists():
        print(f"  ⚠ Missing Sellerboard export: {filepath}")
        return sku_data

    # Resolve date range (defaults to last 90 days ending today)
    today = datetime.now().date()
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_dt = today

    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_dt = end_dt - timedelta(days=90)

    # Sellerboard automated reports use comma delimiters (manual exports use semicolon)
    with filepath.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        # Auto-detect delimiter (try comma first, then semicolon)
        first_line = f.readline()
        f.seek(0)
        delimiter = "," if "," in first_line else ";"
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # Filter by date range
            date_str = (row.get("Date") or "").strip()
            if date_str:
                try:
                    row_date = datetime.strptime(date_str, "%d/%m/%Y").date()  # DD/MM/YYYY format
                except:
                    try:
                        row_date = datetime.strptime(date_str, "%m/%d/%Y").date()  # MM/DD/YYYY format
                    except:
                        continue  # Skip rows with invalid dates
                
                if row_date < start_dt or row_date > end_dt:
                    continue  # Skip rows outside date range
            
            # Filter by marketplace (US only by default)
            marketplace = (row.get("Marketplace") or "").strip()
            if marketplace_filter and marketplace != marketplace_filter:
                continue
            
            sku = (row.get("SKU") or "").strip()
            if not sku:
                continue

            # Totals: organic + PPC (PPC already includes SponsoredProducts + SponsoredDisplay)
            # NOTE: SalesPPC = SalesSponsoredProducts + SalesSponsoredDisplay (already aggregated)
            # Adding them separately would TRIPLE-COUNT ad sales!
            units = (
                _to_int(row.get("UnitsOrganic"))
                + _to_int(row.get("UnitsPPC"))
            )

            revenue = (
                _to_float(row.get("SalesOrganic"))
                + _to_float(row.get("SalesPPC"))
            )

            agg = sku_data.get(sku)
            if not agg:
                agg = SkuAgg()
                sku_data[sku] = agg
            agg.units += units
            agg.revenue += revenue

    return sku_data


def process_legacy_sales_csv(filepath: Path) -> Dict[str, SkuAgg]:
    """Legacy processor for older exports that already had SKU/Units/Revenue."""
    sku_data: Dict[str, SkuAgg] = {}

    with filepath.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = (
                row.get("SKU")
                or row.get("sku")
                or row.get("Seller SKU")
                or row.get("ASIN")
                or ""
            ).strip()
            if not sku:
                continue

            units = (
                row.get("Units")
                or row.get("units")
                or row.get("Quantity")
                or row.get("Units Sold")
                or "0"
            )
            revenue = (
                row.get("Revenue")
                or row.get("revenue")
                or row.get("Sales")
                or row.get("Total Sales")
                or "0"
            )

            agg = sku_data.get(sku)
            if not agg:
                agg = SkuAgg()
                sku_data[sku] = agg
            agg.units += _to_int(units)
            agg.revenue += _to_float(revenue)

    return sku_data


def update_velocity_data(
    input_dir: Path = DATA_DIR,
    out_path: Path = DATA_DIR.parent / "sku_velocity.json",
    period_days: int = 90,
) -> dict:
    velocity_data = {
        "timestamp": datetime.now().isoformat(),
        "period_days": period_days,
        "source": "sellerboard",
        "brands": {},
    }

    for brand in BRANDS:
        # Preferred filename
        dash_path = input_dir / f"{brand}_dashboard_by_product_90d.csv"
        legacy_path = input_dir / f"{brand}_sales_90d.csv"

        if dash_path.exists():
            # Filter to last N days (default: 90) and Amazon.com (US) only
            end_dt = datetime.now().date()
            start_dt = end_dt - timedelta(days=period_days)
            sku_data = process_dashboard_by_product_csv(
                dash_path,
                start_date=start_dt.isoformat(),
                end_date=end_dt.isoformat(),
                marketplace_filter="Amazon.com",
            )
            source_file = dash_path.name
        elif legacy_path.exists():
            sku_data = process_legacy_sales_csv(legacy_path)
            source_file = legacy_path.name
        else:
            print(f"  ⚠ No export found for {brand} in {input_dir}")
            continue

        brand_velocity = {}
        for sku, agg in sku_data.items():
            brand_velocity[sku] = {
                "units_90d": int(agg.units),
                "revenue_90d": round(float(agg.revenue), 2),
                "daily_velocity": round(float(agg.units) / period_days, 4),
                "daily_revenue": round(float(agg.revenue) / period_days, 4),
            }

        velocity_data["brands"][brand] = {
            "source_file": source_file,
            "total_skus": len(brand_velocity),
            "total_units": sum(v["units_90d"] for v in brand_velocity.values()),
            "total_revenue": round(sum(v["revenue_90d"] for v in brand_velocity.values()), 2),
            "skus": brand_velocity,
        }
        print(f"✓ {brand}: {len(brand_velocity)} SKUs processed ({source_file})")

    out_path.write_text(json.dumps(velocity_data, indent=2))
    print(f"\n✓ Velocity data saved to {out_path}")
    return velocity_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--process", action="store_true", help="Process existing exports into sku_velocity.json")
    parser.add_argument("--input-dir", default=str(DATA_DIR))
    parser.add_argument("--out", default=str(DATA_DIR.parent / "sku_velocity.json"))
    parser.add_argument("--period-days", type=int, default=90)
    args = parser.parse_args()

    if args.process:
        update_velocity_data(Path(args.input_dir), Path(args.out), args.period_days)
    else:
        print(get_export_instructions())
