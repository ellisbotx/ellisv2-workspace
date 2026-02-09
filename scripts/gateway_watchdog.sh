#!/bin/bash
# OpenClaw Gateway Watchdog
# Checks if gateway is responding, auto-restarts if down, notifies #alerts
# Designed to run via launchd every 60 seconds

LOGFILE="/Users/ellisbot/.openclaw/workspace/logs/watchdog.log"
GATEWAY_URL="http://127.0.0.1:18789"
ALERTS_CHANNEL="1468702879672959157"
MAX_LOG_LINES=500

# Ensure log directory exists
mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S CST') | $1" >> "$LOGFILE"
}

# Trim log if too large
if [ -f "$LOGFILE" ] && [ "$(wc -l < "$LOGFILE")" -gt "$MAX_LOG_LINES" ]; then
    tail -n 250 "$LOGFILE" > "${LOGFILE}.tmp" && mv "${LOGFILE}.tmp" "$LOGFILE"
fi

# Check if gateway is responding (2 second timeout)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 --max-time 5 "$GATEWAY_URL" 2>/dev/null)

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 500 ] 2>/dev/null; then
    # Gateway is up - silent success (don't spam the log)
    exit 0
fi

# Gateway is down - log it
log "⚠️  Gateway DOWN (HTTP: ${HTTP_CODE:-timeout}). Attempting restart..."

# Wait 5 seconds and check again (avoid false positives during normal restarts)
sleep 5
HTTP_CODE2=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 --max-time 5 "$GATEWAY_URL" 2>/dev/null)

if [ "$HTTP_CODE2" -ge 200 ] && [ "$HTTP_CODE2" -lt 500 ] 2>/dev/null; then
    log "✅ Gateway recovered on second check (was likely restarting). No action needed."
    exit 0
fi

# Confirmed down - restart
log "🔄 Confirmed down. Restarting gateway..."

# Try openclaw gateway restart first
RESTART_OUTPUT=$(openclaw gateway restart 2>&1)
RESTART_EXIT=$?

if [ $RESTART_EXIT -eq 0 ]; then
    log "✅ Gateway restart command succeeded."
else
    log "❌ Gateway restart failed (exit $RESTART_EXIT): $RESTART_OUTPUT"
    # Try launchctl as fallback
    log "🔄 Trying launchctl restart as fallback..."
    launchctl kickstart -k "gui/$(id -u)/com.openclaw.gateway" 2>&1
fi

# Wait for gateway to come back up (up to 30 seconds)
for i in $(seq 1 6); do
    sleep 5
    HTTP_CHECK=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 --max-time 5 "$GATEWAY_URL" 2>/dev/null)
    if [ "$HTTP_CHECK" -ge 200 ] && [ "$HTTP_CHECK" -lt 500 ] 2>/dev/null; then
        DOWNTIME=$((i * 5))
        log "✅ Gateway back online after ${DOWNTIME}s"
        
        # Send Discord notification
        TIMESTAMP=$(date '+%Y-%m-%d %I:%M %p CST')
        openclaw message send \
            --channel discord \
            --target "$ALERTS_CHANNEL" \
            --message "🔄 **Gateway Auto-Restart**

The OpenClaw gateway was detected as down and has been automatically restarted.

**Time:** ${TIMESTAMP}
**Recovery time:** ${DOWNTIME} seconds
**Status:** ✅ Back online

_This message was sent by the gateway watchdog._" 2>/dev/null
        
        log "📢 Notification sent to #alerts"
        exit 0
    fi
done

# Failed to recover
log "❌ Gateway failed to recover after 30 seconds!"

# Try to notify via Discord CLI directly (gateway might still be booting)
sleep 10
openclaw message send \
    --channel discord \
    --target "$ALERTS_CHANNEL" \
    --message "🚨 **Gateway Recovery Failed**

The OpenClaw gateway was detected as down. Auto-restart was attempted but the gateway has not recovered after 40 seconds.

**Time:** $(date '+%Y-%m-%d %I:%M %p CST')
**Status:** ❌ Still down

Manual intervention may be required. Check the Mac mini.

_This message was sent by the gateway watchdog._" 2>/dev/null

log "📢 Failure notification sent to #alerts"
exit 1
