#!/bin/bash
# Todoist event polling — runs every 5 minutes via LaunchAgent
# Detects task adds/completions/updates and posts changes to #tasks
# No message posted when nothing changed (anti-spam).

set -euo pipefail

SCRIPTS="/Users/ellisbot/.openclaw/workspace/scripts"
LOGS="/Users/ellisbot/.openclaw/workspace/logs"
CHANNEL="1470181819067531500"
LOG="$LOGS/todoist_poll.log"

mkdir -p "$LOGS"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Poll starting..." >> "$LOG"

# Run detection script
MESSAGE=$(python3 "$SCRIPTS/todoist_poll_events.py" 2>>"$LOG") || true
EXIT_CODE=${PIPESTATUS[0]:-$?}

if [ -n "$MESSAGE" ] && echo "$MESSAGE" | grep -q "Todoist Update"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Changes detected, posting to #tasks" >> "$LOG"
    openclaw message send --channel discord --target "$CHANNEL" --message "$MESSAGE" >> "$LOG" 2>&1 || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Posted." >> "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No changes." >> "$LOG"
fi
