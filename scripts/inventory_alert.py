#!/usr/bin/env python3
"""
Daily Inventory Countdown Alert
Calculates days of inventory remaining and posts alerts to Discord #inventory.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/Users/ellisbot/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))
from discord_utils import post_inventory

BRANDS = {
    "blackowned": {"inventory": "blackowned_inventory.json", "label": "Black Owned"},
    "cardplug": {"inventory": "cardplug_inventory.json", "label": "Card Plug"},
    "kinfolk": {"inventory": "kinfolk_inventory.json", "label": "Kinfolk"},
}

URGENT_DAYS = 90
WARNING_DAYS = 120
PLAN_DAYS = 190
LEAD_TIME_DAYS = 100
MIN_MOQ = 500
TARGET_DAYS = 90  # reorder to cover this many days


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}")
        return None


def load_liquidation_asins():
    path = WORKSPACE / "data" / "liquidation_asins.txt"
    asins = set()
    if not path.exists():
        return asins
    for line in path.read_text().splitlines():
        # Extract ASIN (B0...) from lines like "Street Kings - B0F4YFM8DG"
        parts = line.strip().split(" - ")
        if len(parts) >= 2:
            asin = parts[-1].strip()
            if asin.startswith("B0"):
                asins.add(asin)
    return asins


def build_inventory_lookup(inv_data):
    """Map sellerSku -> fulfillableQuantity from inventory JSON."""
    lookup = {}
    if not inv_data or "items" not in inv_data:
        return lookup
    for item in inv_data["items"]:
        sku = item.get("sellerSku", "")
        qty = item.get("inventoryDetails", {}).get("fulfillableQuantity", 0)
        asin = item.get("asin", "")
        lookup[sku] = {"on_hand": qty, "asin": asin}
    return lookup


def main():
    velocity_data = load_json(WORKSPACE / "data" / "sku_velocity.json")
    if not velocity_data:
        print("ERROR: Could not load sku_velocity.json")
        return

    liquidation_asins = load_liquidation_asins()
    print(f"Loaded {len(liquidation_asins)} liquidation ASINs to exclude")

    urgent_items = []
    warning_items = []
    plan_items = []

    for brand_key, brand_info in BRANDS.items():
        inv_data = load_json(WORKSPACE / "data" / brand_info["inventory"])
        inv_lookup = build_inventory_lookup(inv_data)

        brand_velocity = velocity_data.get("brands", {}).get(brand_key, {}).get("skus", {})

        for sku, vel_info in brand_velocity.items():
            daily_vel = vel_info.get("daily_velocity", 0)
            if daily_vel <= 0:
                continue  # skip dead inventory

            # Get inventory from FBA data
            inv_info = inv_lookup.get(sku, {})
            on_hand = inv_info.get("on_hand", 0)
            asin = inv_info.get("asin", "")

            # Skip liquidation ASINs
            if asin in liquidation_asins:
                continue

            days_remaining = on_hand / daily_vel if daily_vel > 0 else float('inf')

            # Get product name from sellerboard CSV (use SKU as fallback)
            name = sku

            # Calculate recommended order qty
            order_qty = max(MIN_MOQ, int((TARGET_DAYS * daily_vel) - on_hand + (LEAD_TIME_DAYS * daily_vel)))
            order_qty = max(order_qty, 0)

            entry = {
                "sku": sku,
                "asin": asin,
                "brand": brand_info["label"],
                "on_hand": on_hand,
                "daily_vel": round(daily_vel, 2),
                "days_remaining": round(days_remaining, 1),
                "order_qty": max(MIN_MOQ, order_qty) if days_remaining < PLAN_DAYS else 0,
            }

            if days_remaining < URGENT_DAYS:
                urgent_items.append(entry)
            elif days_remaining < WARNING_DAYS:
                warning_items.append(entry)
            elif days_remaining < PLAN_DAYS:
                plan_items.append(entry)

    # Sort each by days remaining
    urgent_items.sort(key=lambda x: x["days_remaining"])
    warning_items.sort(key=lambda x: x["days_remaining"])
    plan_items.sort(key=lambda x: x["days_remaining"])

    # Build Discord message
    now = datetime.now().strftime("%b %d, %Y")
    total_flagged = len(urgent_items) + len(warning_items) + len(plan_items)

    if total_flagged == 0:
        msg = f"📦 **Inventory Countdown — {now}**\n\n✅ All active SKUs have 190+ days of inventory. No action needed."
        post_inventory(msg)
        print("All clear - no inventory alerts")
        return

    msg = f"📦 **Inventory Countdown — {now}**\n{total_flagged} SKUs need attention\n"

    def format_section(items, emoji, label):
        if not items:
            return ""
        section = f"\n{emoji} **{label}** ({len(items)} SKUs)\n"
        for i in items[:15]:  # Cap at 15 per section for Discord limits
            section += (
                f"• **{i['sku']}** ({i['brand']})\n"
                f"  ASIN: `{i['asin']}` | On-hand: **{i['on_hand']}** | "
                f"Vel: {i['daily_vel']}/day | **{i['days_remaining']} days left**"
            )
            if i['order_qty'] > 0:
                section += f" | Order: **{i['order_qty']}** units"
            section += "\n"
        if len(items) > 15:
            section += f"  ...and {len(items) - 15} more\n"
        return section

    msg += format_section(urgent_items, "🔴", f"URGENT (< {URGENT_DAYS} days)")
    msg += format_section(warning_items, "🟡", f"WARNING (< {WARNING_DAYS} days)")
    msg += format_section(plan_items, "🔵", f"PLAN (< {PLAN_DAYS} days — order now for {LEAD_TIME_DAYS}-day lead time)")

    # Post to Discord
    if post_inventory(msg):
        print(f"Posted inventory alert: {total_flagged} SKUs flagged")
    else:
        print("Failed to post to Discord")
        print(msg)


if __name__ == "__main__":
    main()
