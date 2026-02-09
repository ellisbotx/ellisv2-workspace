# Cron Schedule — Proactive Automation Scripts

All times in **CST (America/Chicago)**.

## Daily Scripts

| Time | Script | Channel | Description |
|------|--------|---------|-------------|
| 7:00 AM | `inventory_alert.py` | #inventory | Inventory countdown alerts (urgent/warning/plan) |
| 7:05 AM | `sales_anomaly.py` | #alerts / #reports | Velocity anomaly detection (drops >40%, spikes >50%) |

## Weekly Scripts (Mondays)

| Time | Script | Channel | Description |
|------|--------|---------|-------------|
| 7:00 AM | `weekly_health_report.py` | #reports | Business health: revenue, units, profit, top/bottom SKUs |
| 7:15 AM | `reorder_recommendations.py` | #inventory | Ranked reorder list with order quantities |

## Cron Jobs to Create

```crontab
# Daily: Inventory countdown alert (7:00 AM CST)
0 7 * * * cd /Users/ellisbot/.openclaw/workspace && /usr/bin/python3 scripts/inventory_alert.py >> data/sellerboard/cron.log 2>&1

# Daily: Sales anomaly detection (7:05 AM CST)
5 7 * * * cd /Users/ellisbot/.openclaw/workspace && /usr/bin/python3 scripts/sales_anomaly.py >> data/sellerboard/cron.log 2>&1

# Weekly: Business health report (Monday 7:00 AM CST)
0 7 * * 1 cd /Users/ellisbot/.openclaw/workspace && /usr/bin/python3 scripts/weekly_health_report.py >> data/sellerboard/cron.log 2>&1

# Weekly: Reorder recommendations (Monday 7:15 AM CST)
15 7 * * 1 cd /Users/ellisbot/.openclaw/workspace && /usr/bin/python3 scripts/reorder_recommendations.py >> data/sellerboard/cron.log 2>&1
```

## Notes

- Scripts use `discord_utils.py` for posting via `openclaw message send`
- Liquidation ASINs (65 total) are automatically excluded from all reports
- Dead inventory (0 velocity) is skipped
- All scripts handle missing data gracefully
- Discord posting uses the `openclaw` CLI — requires the gateway to be running
