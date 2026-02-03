# Sellerboard Export Automation

## Overview

Automated daily export of Sellerboard "Dashboard by product" reports for 3 brands with processing into unified JSON format for dashboards.

## Components

### 1. `sellerboard_auto_export.py`
Browser automation script using Playwright that:
- ✅ Logs into Sellerboard using 1Password credentials
- ✅ Switches between 3 brands (Black Owned/srgrier45, Card Plug, Kinfolk)  
- ✅ Navigates to Reports → Dashboard by product
- ⚠️ Downloads CSV exports (needs refinement - see Status below)
- ✅ Processes CSVs into `sku_velocity.json`

### 2. `sellerboard_export.py`
CSV processing script that:
- Reads Dashboard by product CSV exports
- Aggregates units & revenue across all sales channels
- Calculates daily velocity metrics  
- Outputs to `/Users/ellisbot/.openclaw/workspace/data/sku_velocity.json`

## Usage

### Automated Export (Work in Progress)

```bash
# Dry run (test navigation without downloading)
python3 sellerboard_auto_export.py --dry-run

# Download for all 3 brands
python3 sellerboard_auto_export.py

# Download for single brand
python3 sellerboard_auto_export.py --brand kinfolk

# Download without processing (for debugging)
python3 sellerboard_auto_export.py --no-process

# Run in headless mode
python3 sellerboard_auto_export.py --headless
```

### Manual Export + Automated Processing

Until the download automation is fully refined, you can use this hybrid approach:

1. **Manual Download** (5 minutes for all 3 brands):
   - Login to https://app.sellerboard.com
   - For each brand (switch using dropdown in top-right):
     - Go to Reports → Dashboard by product
     - Set date range: Last 90 days
     - Download as CSV
     - Save to `/Users/ellisbot/.openclaw/workspace/data/sellerboard/{brand}_dashboard_by_product_90d.csv`
   - Brand filename mappings:
     - Summary Dashboard (srgrier45) → `blackowned_dashboard_by_product_90d.csv`
     - CardPlug → `cardplug_dashboard_by_product_90d.csv`
     - Kinfolk → `kinfolk_dashboard_by_product_90d.csv`

2. **Automated Processing**:
   ```bash
   python3 sellerboard_export.py --process
   ```

## Output Format

`/Users/ellisbot/.openclaw/workspace/data/sku_velocity.json`:

```json
{
  "timestamp": "2026-02-02T14:55:00.000000",
  "period_days": 90,
  "source": "sellerboard",
  "brands": {
    "blackowned": {
      "source_file": "blackowned_dashboard_by_product_90d.csv",
      "total_skus": 56,
      "total_units": 1234,
      "total_revenue": 45678.90,
      "skus": {
        "SKU-123": {
          "units_90d": 100,
          "revenue_90d": 1250.00,
          "daily_velocity": 1.1111,
          "daily_revenue": 13.8889
        }
      }
    }
  }
}
```

## Files & Directories

```
/Users/ellisbot/.openclaw/workspace/
├── scripts/
│   ├── sellerboard_auto_export.py     # Browser automation
│   ├── sellerboard_export.py          # CSV processing
│   └── README_SELLERBOARD.md          # This file
└── data/
    ├── sku_velocity.json              # Unified output
    └── sellerboard/
        ├── blackowned_dashboard_by_product_90d.csv
        ├── cardplug_dashboard_by_product_90d.csv
        ├── kinfolk_dashboard_by_product_90d.csv
        ├── auto_export.log            # Automation logs
        └── screenshots/               # Debug screenshots
```

## Status & Testing

### ✅ Working
- 1Password credential retrieval
- Sellerboard login automation
- Brand switching (all 3 brands)
- Navigation to Reports → Dashboard by product
- CSV processing (all 3 brands)
- JSON output generation
- Error handling & logging
- Screenshot capture on failures

### ⚠️ Needs Refinement
- Download button interaction (Sellerboard UI uses complex Angular/React components)
- Date range selection (hidden inputs, not standard form fields)

### Test Results

**Dry Run Test** (2026-02-02 14:51):
```
✓ Login successful
✓ Switched to Summary Dashboard
✓ Switched to CardPlug  
✓ Switched to Kinfolk
✓ Navigated to Dashboard by product (all brands)
⚠ Date range selection: using default (works for 90 days)
⚠ Download: timeout waiting for download trigger
```

**CSV Processing Test** (2026-02-02 14:55):
```
✓ blackowned: 56 SKUs processed
✓ cardplug: 72 SKUs processed  
✓ kinfolk: 46 SKUs processed
✓ Total: 174 SKUs, sku_velocity.json created
```

## Cron Setup

### Daily Automated Processing (with manual downloads)

```bash
# Edit crontab
crontab -e

# Add this line to run at 2 AM CST daily
0 2 * * * cd /Users/ellisbot/.openclaw/workspace/scripts && /usr/bin/python3 sellerboard_export.py --process >> /Users/ellisbot/.openclaw/workspace/data/sellerboard/cron.log 2>&1
```

### Future: Fully Automated (once download is refined)

```bash
# Run automation at 2 AM CST daily
0 2 * * * cd /Users/ellisbot/.openclaw/workspace/scripts && /usr/bin/python3 sellerboard_auto_export.py --headless >> /Users/ellisbot/.openclaw/workspace/data/sellerboard/cron.log 2>&1
```

## Troubleshooting

### Issue: Download times out
**Solution**: Use hybrid approach (manual download + automated processing) until download automation is refined.

### Issue: "op: not found" when running automated script
**Solution**: Ensure 1Password CLI is installed and you're signed in:
```bash
brew install 1password-cli
op signin
```

### Issue: Missing playwright
**Solution**:
```bash
pip3 install playwright
python3 -m playwright install chromium
```

### Issue: JSON output missing a brand
**Solution**: Check that the CSV file exists and matches the expected filename pattern in `/Users/ellisbot/.openclaw/workspace/data/sellerboard/`

## Debugging

View automation logs:
```bash
tail -f /Users/ellisbot/.openclaw/workspace/data/sellerboard/auto_export.log
```

View latest screenshots:
```bash
ls -lt /Users/ellisbot/.openclaw/workspace/data/sellerboard/screenshots/ | head -10
```

Test single brand with verbose logging:
```bash
python3 sellerboard_auto_export.py --brand kinfolk --dry-run
```

## Next Steps for Full Automation

1. **Inspect Sellerboard's Export Page**:
   - Open DevTools on the Dashboard by product export page
   - Find the actual download button element and its event handlers
   - Determine if it uses a direct link or JavaScript-triggered download

2. **Alternative Approaches**:
   - Check if Sellerboard has an unofficial API
   - Use browser DevTools to capture the download request and replicate it
   - Contact Sellerboard support about API access

3. **Simplification**:
   - Since manual downloads work well and take only ~5 minutes for all 3 brands
   - Consider keeping hybrid approach: manual download daily, automated processing
   - Set calendar reminder for daily 1:55 AM downloads before 2 AM processing cron

## Credits

- **Created**: 2026-02-02
- **Status**: Hybrid solution (manual download + automated processing) operational
- **Next Review**: After testing Sellerboard's export page structure more thoroughly
