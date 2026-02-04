#!/bin/bash
# Sellerboard Daily Email Fetch & Dashboard Update
# Runs at 3 AM to fetch automated reports from email

set -e

WORKSPACE="/Users/ellisbot/.openclaw/workspace"
LOG_FILE="$WORKSPACE/data/sellerboard/email_fetch.log"

echo "========================================" >> "$LOG_FILE"
echo "$(date): Starting email fetch..." >> "$LOG_FILE"

cd "$WORKSPACE"

# Fetch CSVs from email (Sellerboard automated reports)
echo "$(date): Fetching Sellerboard exports from email..." >> "$LOG_FILE"
python3 scripts/gmail_fetch_sellerboard.py >> "$LOG_FILE" 2>&1

# Check if we got all 3 brands
if [ -f "data/sellerboard/blackowned_dashboard_by_product_90d.csv" ] && \
   [ -f "data/sellerboard/cardplug_dashboard_by_product_90d.csv" ] && \
   [ -f "data/sellerboard/kinfolk_dashboard_by_product_90d.csv" ]; then
    
    echo "$(date): ✓ All 3 brand CSVs found" >> "$LOG_FILE"
    
    # Process into velocity data
    echo "$(date): Processing velocity data..." >> "$LOG_FILE"
    python3 scripts/sellerboard_export.py --process >> "$LOG_FILE" 2>&1
    
    # Update dashboards
    echo "$(date): Updating dashboards..." >> "$LOG_FILE"
    python3 scripts/generate_profitability_page.py >> "$LOG_FILE" 2>&1
    python3 scripts/generate_products_page.py >> "$LOG_FILE" 2>&1
    python3 scripts/update_overview.py >> "$LOG_FILE" 2>&1
    
    echo "$(date): ✓ Dashboard update complete" >> "$LOG_FILE"
else
    echo "$(date): ⚠️ Missing CSVs - will retry at 7 AM" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Complete" >> "$LOG_FILE"
