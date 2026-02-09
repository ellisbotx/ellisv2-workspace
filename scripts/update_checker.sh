#!/bin/bash
# OpenClaw Update Checker - Zero tokens, pure bash
# Checks for available updates and notifies #system if one exists

SYSTEM_CHANNEL="1468708512539349155"
LOGFILE="/Users/ellisbot/.openclaw/workspace/logs/update_checker.log"

mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S CST') | $1" >> "$LOGFILE"
}

# Get current version
CURRENT=$(openclaw --version 2>/dev/null)
if [ -z "$CURRENT" ]; then
    log "❌ Could not get current version"
    exit 1
fi

# Check npm for latest version
LATEST=$(npm view openclaw version 2>/dev/null)
if [ -z "$LATEST" ]; then
    log "❌ Could not check npm for latest version"
    exit 1
fi

if [ "$CURRENT" = "$LATEST" ]; then
    log "✅ Up to date: $CURRENT"
    exit 0
fi

# Update available
log "🔄 Update available: $CURRENT → $LATEST"

openclaw message send \
    --channel discord \
    --target "$SYSTEM_CHANNEL" \
    --message "🔄 **OpenClaw Update Available**

**Current:** \`$CURRENT\`
**Available:** \`$LATEST\`

Reply in any channel to approve the update." 2>/dev/null

log "📢 Notification sent to #system"
