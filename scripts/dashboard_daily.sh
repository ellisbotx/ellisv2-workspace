#!/bin/bash
# Daily Trifecta dashboard build script
# Runs all generators in the correct order and writes a timestamped log.
#
# Intended cron (3:00 AM daily):
#   0 3 * * * /Users/ellisbot/.openclaw/workspace/scripts/dashboard_daily.sh

set -euo pipefail

WORKDIR="/Users/ellisbot/.openclaw/workspace"
SCRIPT_DIR="$WORKDIR/scripts"
LOG_DIR="$WORKDIR/data/logs"
LOG_FILE="$LOG_DIR/dashboard_daily.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Dashboard Daily Build Started"
log "=========================================="

cd "$WORKDIR"

log "1/5 inventory_tracker.py"
python3 "$SCRIPT_DIR/inventory_tracker.py" >> "$LOG_FILE" 2>&1

log "2/5 reorder_tracker.py"
python3 "$SCRIPT_DIR/reorder_tracker.py" >> "$LOG_FILE" 2>&1

log "3/5 update_overview.py"
python3 "$SCRIPT_DIR/update_overview.py" >> "$LOG_FILE" 2>&1

log "4/5 generate_dashboard.py (inventory.html)"
python3 "$SCRIPT_DIR/generate_dashboard.py" >> "$LOG_FILE" 2>&1

log "5/5 generate_products_page.py (products.html)"
python3 "$SCRIPT_DIR/generate_products_page.py" >> "$LOG_FILE" 2>&1

log "✓ Dashboard daily build complete"
log "Outputs:"
log "  - $WORKDIR/data/inventory_dashboard.json"
log "  - $WORKDIR/data/reorder_report.json"
log "  - $WORKDIR/trifecta/index.html"
log "  - $WORKDIR/trifecta/inventory.html"
log "  - $WORKDIR/trifecta/products.html"
log "=========================================="
