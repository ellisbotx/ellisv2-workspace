#!/bin/bash
# Daily Sellerboard processing script
# Processes existing CSV exports into unified sku_velocity.json
#
# Usage: Run manually or via cron at 2 AM CST daily
# Cron: 0 2 * * * /Users/ellisbot/.openclaw/workspace/scripts/sellerboard_daily.sh

set -e

SCRIPT_DIR="/Users/ellisbot/.openclaw/workspace/scripts"
DATA_DIR="/Users/ellisbot/.openclaw/workspace/data/sellerboard"
LOG_FILE="$DATA_DIR/daily_processing.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Sellerboard Daily Processing Started"
log "=========================================="

# Check if CSV files exist
REQUIRED_FILES=(
    "blackowned_dashboard_by_product_90d.csv"
    "cardplug_dashboard_by_product_90d.csv"
    "kinfolk_dashboard_by_product_90d.csv"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$DATA_DIR/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    log "WARNING: Missing CSV files:"
    for file in "${MISSING_FILES[@]}"; do
        log "  - $file"
    done
    log "Please download missing files from Sellerboard"
    log "See: $SCRIPT_DIR/README_SELLERBOARD.md for instructions"
fi

# Check file ages (warn if older than 2 days)
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$DATA_DIR/$file" ]; then
        FILE_AGE=$(( ($(date +%s) - $(stat -f %m "$DATA_DIR/$file")) / 86400 ))
        if [ $FILE_AGE -gt 2 ]; then
            log "WARNING: $file is $FILE_AGE days old (may be stale)"
        else
            log "✓ $file is up to date ($FILE_AGE days old)"
        fi
    fi
done

# Run processing
log ""
log "Processing CSV files..."
cd "$SCRIPT_DIR"

if python3 sellerboard_export.py --process >> "$LOG_FILE" 2>&1; then
    log "✓ Processing complete"
    log "✓ Output: /Users/ellisbot/.openclaw/workspace/data/sku_velocity.json"
    
    # Show summary
    if [ -f "/Users/ellisbot/.openclaw/workspace/data/sku_velocity.json" ]; then
        TOTAL_SKUS=$(python3 -c "import json; d=json.load(open('/Users/ellisbot/.openclaw/workspace/data/sku_velocity.json')); print(sum(b['total_skus'] for b in d['brands'].values()))")
        log "✓ Total SKUs processed: $TOTAL_SKUS"
    fi
else
    log "✗ Processing failed - check logs above"
    exit 1
fi

# Generate Profitability Dashboard
log ""
log "Generating Profitability Dashboard..."
if python3 generate_profitability_page.py >> "$LOG_FILE" 2>&1; then
    log "✓ Profitability page generated"
    log "✓ Output: /Users/ellisbot/.openclaw/workspace/trifecta/profitability.html"
else
    log "✗ Profitability page generation failed"
fi

log ""
log "=========================================="
log "Sellerboard Daily Processing Complete"
log "=========================================="
