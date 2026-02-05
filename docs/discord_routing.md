# Discord Channel Routing

## Overview

All automation, reports, and alerts are now routed to specific Discord channels. This keeps your workspace organized and lets you control notifications per topic.

## Channel Map

| Channel | Purpose | Notification |
|---------|---------|--------------|
| **#general💬** | Main conversation, default chat | All Messages |
| **#alerts🚨** | ASIN suppressions, stockouts, critical issues | All Messages |
| **#reports📊** | Daily ASIN checks, weekly summaries, performance reports | Muted/Mentions Only |
| **#dashboard📊** | Trifecta updates, high-level metrics | Muted |
| **#inventory📦** | Reorder recommendations, stock levels, FBA alerts | Mentions Only |
| **#products🎴** | SKU performance, kill/keep decisions, listing optimization | Mentions Only |
| **#automation⚙️** | Script execution logs, cron results, integration status | Muted |
| **#analytics📈** | Deep-dive analysis, trend reports, competitor insights | Muted |
| **#orders📦** | Etsy→MCF automation, PO tracking, shipment updates | Mentions Only |
| **#suppliers🏭** | Vendor communications, quotes, quality issues | Mentions Only |
| **#creative🎨** | New game concepts, title brainstorming, design feedback | Muted |
| **#finance💰** | P&L analysis, cash flow, profitability reviews | Mentions Only |
| **#system🧠** | Memory updates, new skills, agent evolution, meta-learning | Mentions Only |
| **#done✅** | Completed projects, decision logs, archives | Muted |

## What Goes Where

### Daily Automation (1 AM CST)
- **ASIN checker** → #reports (summary) + #alerts (if suppressions found)

### Future Automation
- **Reorder recommendations** → #inventory
- **Etsy→MCF order logs** → #orders
- **Supplier PO tracking** → #suppliers
- **Weekly SKU performance** → #products
- **Monthly P&L reports** → #finance
- **Deep analysis** → #analytics
- **Memory consolidation** → #system (weekly summaries)
- **New skills installed** → #system
- **Agent config changes** → #system
- **Task completions** → #done

### Manual Posts
- **General conversation** → #general
- **Product ideas** → #creative
- **Dashboard updates** → #dashboard

## Configuration

Channel IDs and routing rules: `/workspace/config/discord_channels.json`

Scripts use the `discord_utils.py` helper module to post messages:

```python
from discord_utils import post_alert, post_report, post_inventory

# Post to #alerts
post_alert("🚨 Critical issue detected!")

# Post to #reports (silent)
post_report("📊 Daily summary", silent=True)

# Post to #inventory
post_inventory("📦 Reorder recommendation: XYZ needs 500 units")
```

## How to Change Routing

Edit `/workspace/config/discord_channels.json` to update channel IDs or routing rules.

Scripts will automatically use the updated configuration.

## Testing

Run `/workspace/scripts/discord_utils.py` directly to test posting to channels:

```bash
python3 /Users/ellisbot/.openclaw/workspace/scripts/discord_utils.py
```

This will send test messages to #reports and #automation.
