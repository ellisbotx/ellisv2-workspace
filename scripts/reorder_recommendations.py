#!/usr/bin/env python3
"""
Weekly Reorder Recommendations
SKUs needing reorder ranked by profit contribution, urgency, sell-through rate.
Posts to #inventory every Monday 7:15 AM.
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

PLAN_DAYS = 190
LEAD_TIME = 100
TARGET_DAYS = 90
MIN_MOQ = 500

# Scoring weights
W_PROFIT = 0.50
W_URGENCY = 0.35
W_SELLTHROUGH = 0.15


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


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


def build_inventory_lookup(inv_data):
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
    candidates = []

    # Collect all revenue for profit contribution calc
    all_revenues = []
    for brand_key, brand_info in BRANDS.items():
        brand_vel = velocity_data.get("brands", {}).get(brand_key, {}).get("skus", {})
        for sku, vel_info in brand_vel.items():
            dr = vel_info.get("daily_revenue", 0)
            if dr > 0:
                all_revenues.append(dr)
    total_daily_revenue = sum(all_revenues) if all_revenues else 1

    for brand_key, brand_info in BRANDS.items():
        inv_data = load_json(WORKSPACE / "data" / brand_info["inventory"])
        inv_lookup = build_inventory_lookup(inv_data)
        brand_vel = velocity_data.get("brands", {}).get(brand_key, {}).get("skus", {})

        for sku, vel_info in brand_vel.items():
            daily_vel = vel_info.get("daily_velocity", 0)
            daily_rev = vel_info.get("daily_revenue", 0)
            if daily_vel <= 0:
                continue

            inv_info = inv_lookup.get(sku, {})
            on_hand = inv_info.get("on_hand", 0)
            asin = inv_info.get("asin", "")

            if asin in liquidation_asins:
                continue

            days_remaining = on_hand / daily_vel
            if days_remaining >= PLAN_DAYS:
                continue  # doesn't need reorder

            # Order qty: enough for TARGET_DAYS + LEAD_TIME coverage minus current stock
            need = (TARGET_DAYS + LEAD_TIME) * daily_vel - on_hand
            order_qty = max(MIN_MOQ, int(need))

            # Scoring
            profit_score = daily_rev / total_daily_revenue  # normalized 0-1
            urgency_score = max(0, 1 - (days_remaining / PLAN_DAYS))  # 1=urgent, 0=fine
            
            units_90d = vel_info.get("units_90d", 0)
            sellthrough_score = min(1, units_90d / 100) if units_90d else 0  # normalize to ~100 units

            composite = (W_PROFIT * profit_score + W_URGENCY * urgency_score + W_SELLTHROUGH * sellthrough_score)

            candidates.append({
                "sku": sku,
                "asin": asin,
                "brand": brand_info["label"],
                "on_hand": on_hand,
                "daily_vel": round(daily_vel, 2),
                "daily_rev": round(daily_rev, 2),
                "days_remaining": round(days_remaining, 1),
                "order_qty": order_qty,
                "order_cost_est": round(order_qty * 2.50, 2),  # rough $2.50/unit est
                "score": round(composite, 4),
            })

    # Sort by composite score descending
    candidates.sort(key=lambda x: -x["score"])

    now = datetime.now().strftime("%b %d, %Y")

    if not candidates:
        msg = f"📦 **Reorder Recommendations — {now}**\n\n✅ No SKUs need reordering. All active inventory covers 190+ days."
        post_inventory(msg)
        print("No reorders needed")
        return

    total_units = sum(c["order_qty"] for c in candidates)
    total_cost = sum(c["order_cost_est"] for c in candidates)

    msg = f"📦 **Weekly Reorder Recommendations — {now}**\n"
    msg += f"{len(candidates)} SKUs need reordering | Est. {total_units:,} units | ~${total_cost:,.0f}\n"
    msg += f"Ranked by: Profit ({int(W_PROFIT*100)}%) + Urgency ({int(W_URGENCY*100)}%) + Sell-through ({int(W_SELLTHROUGH*100)}%)\n\n"

    for i, c in enumerate(candidates[:20], 1):
        urgency_emoji = "🔴" if c["days_remaining"] < 90 else "🟡" if c["days_remaining"] < 120 else "🔵"
        msg += (
            f"{urgency_emoji} **#{i} {c['sku']}** ({c['brand']})\n"
            f"  ASIN: `{c['asin']}` | Stock: {c['on_hand']} | "
            f"{c['days_remaining']} days left | Vel: {c['daily_vel']}/day\n"
            f"  📦 **Order {c['order_qty']:,} units** (~${c['order_cost_est']:,.0f}) | "
            f"Score: {c['score']}\n"
        )

    if len(candidates) > 20:
        msg += f"\n...and {len(candidates) - 20} more SKUs\n"

    if post_inventory(msg):
        print(f"Posted reorder recommendations: {len(candidates)} SKUs")
    else:
        print("Failed to post")
        print(msg)


if __name__ == "__main__":
    main()
