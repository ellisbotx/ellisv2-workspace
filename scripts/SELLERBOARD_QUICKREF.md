# Sellerboard - Quick Reference Card

## 📥 Daily Manual Download (1:55 AM - 5 minutes)

### Login
```
URL: https://app.sellerboard.com
Email: ellisbotx@gmail.com
Password: (in 1Password - search "sellerboard")
```

### Download for Each Brand
**Top-right dropdown** → Switch brand → **Reports** → **Dashboard by product**

| Brand in UI | Save Filename |
|------------|---------------|
| Summary Dashboard (srgrier45) | `blackowned_dashboard_by_product_90d.csv` |
| CardPlug | `cardplug_dashboard_by_product_90d.csv` |
| Kinfolk | `kinfolk_dashboard_by_product_90d.csv` |

**Save Location**: `/Users/ellisbot/.openclaw/workspace/data/sellerboard/`

Date Range: **Last 90 days** (should be default)  
Format: **CSV**

---

## 🤖 Automated Processing (2:00 AM - Automatic)

Runs via cron automatically.

**Manual trigger**:
```bash
/Users/ellisbot/.openclaw/workspace/scripts/sellerboard_daily.sh
```

**Check status**:
```bash
tail /Users/ellisbot/.openclaw/workspace/data/sellerboard/cron.log
```

**Output**: `/Users/ellisbot/.openclaw/workspace/data/sku_velocity.json`

---

## 🔍 Quick Checks

### Check if CSVs are up to date:
```bash
ls -lht /Users/ellisbot/.openclaw/workspace/data/sellerboard/*.csv | head -3
```

### Verify processing worked:
```bash
cat /Users/ellisbot/.openclaw/workspace/data/sku_velocity.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'✓ {sum(b[\"total_skus\"] for b in d[\"brands\"].values())} SKUs processed at {d[\"timestamp\"]}')"
```

### Manual processing:
```bash
cd /Users/ellisbot/.openclaw/workspace/scripts
python3 sellerboard_export.py --process
```

---

## 🚨 Troubleshooting

### "Missing CSV files" warning
→ Download the missing brand's CSV from Sellerboard

### "File is X days old" warning  
→ Download fresh CSVs from Sellerboard

### Cron not running
```bash
crontab -l  # Check if job exists
tail /var/mail/$USER  # Check for cron errors
```

### Processing errors
```bash
tail -50 /Users/ellisbot/.openclaw/workspace/data/sellerboard/daily_processing.log
```

---

## 📞 Support

**Documentation**: `/Users/ellisbot/.openclaw/workspace/scripts/README_SELLERBOARD.md`  
**Full Summary**: `/Users/ellisbot/.openclaw/workspace/scripts/SELLERBOARD_SUMMARY.md`

**Cron Schedule**: Daily at 2:00 AM CST  
**Expected Runtime**: < 5 seconds  
**Output**: 174 SKUs across 3 brands
