#!/bin/bash
# Daily GitHub backup script
# Automatically commits and pushes workspace changes to GitHub
#
# Runs after dashboard updates complete (4 AM CST)
# Cron: 0 4 * * * /Users/ellisbot/.openclaw/workspace/scripts/git_daily_backup.sh

set -e

WORKDIR="/Users/ellisbot/.openclaw/workspace"
LOG_DIR="$WORKDIR/data/logs"
LOG_FILE="$LOG_DIR/git_backup.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "GitHub Daily Backup Started"
log "=========================================="

cd "$WORKDIR"

# Configure git if not already set
if [ -z "$(git config user.name)" ]; then
    git config user.name "Ellis AI"
    log "✓ Configured git user.name"
fi

if [ -z "$(git config user.email)" ]; then
    git config user.email "ellisbotx@gmail.com"
    log "✓ Configured git user.email"
fi

# Check if there are any changes
if [ -z "$(git status --porcelain)" ]; then
    log "No changes to commit"
    log "=========================================="
    exit 0
fi

# Show what changed
log "Changes detected:"
git status --short | tee -a "$LOG_FILE"

# Add all changes
git add -A
log "✓ Staged all changes"

# Commit with timestamp
COMMIT_MSG="Auto-backup: $(date +'%Y-%m-%d %H:%M CST')"
git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1
log "✓ Committed: $COMMIT_MSG"

# Push to GitHub
# Note: First-time setup requires manual authentication
# Run: git push origin main
# Then enter your GitHub credentials when prompted (they'll be saved in keychain)

if git push origin main >> "$LOG_FILE" 2>&1; then
    log "✓ Pushed to GitHub successfully"
elif git push origin master >> "$LOG_FILE" 2>&1; then
    log "✓ Pushed to GitHub successfully (master branch)"
else
    log "✗ Push failed - authentication may be required"
    log "To fix: Run manually once: cd /Users/ellisbot/.openclaw/workspace && git push"
    log "Then enter your GitHub Personal Access Token when prompted"
    # Don't exit with error - just log and continue
    log "Changes are committed locally but not pushed to GitHub"
fi

log "✓ Backup complete"
log "Repository: https://github.com/ellisbotx/ellisv2-workspace"
log "=========================================="
