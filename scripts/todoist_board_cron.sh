#!/bin/bash
# Todoist summary board — runs hourly via LaunchAgent
# Posts refreshed task board to #tasks and rotates pin (unpin old, pin new).

set -euo pipefail

SCRIPTS="/Users/ellisbot/.openclaw/workspace/scripts"
DATA="/Users/ellisbot/.openclaw/workspace/data"
LOGS="/Users/ellisbot/.openclaw/workspace/logs"
CHANNEL="1470181819067531500"
STATE="$DATA/todoist_board_state.json"
LOG="$LOGS/todoist_board.log"

mkdir -p "$LOGS" "$DATA"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Board refresh starting..." >> "$LOG"

# Generate board
BOARD=$(python3 "$SCRIPTS/todoist_summary_board.py" 2>>"$LOG")
if [ -z "$BOARD" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Failed to generate board." >> "$LOG"
    exit 1
fi

# Read old pin message ID
OLD_PIN_ID=""
if [ -f "$STATE" ]; then
    OLD_PIN_ID=$(python3 -c "
import json, sys
try:
    d = json.load(open('$STATE'))
    print(d.get('last_pin_message_id', '') or '')
except: pass
" 2>/dev/null) || true
fi

# Unpin old board (best effort — may fail if already unpinned)
if [ -n "$OLD_PIN_ID" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Unpinning old: $OLD_PIN_ID" >> "$LOG"
    openclaw message unpin --channel discord --target "$CHANNEL" --message-id "$OLD_PIN_ID" >> "$LOG" 2>&1 || true
fi

# Post new board
RESULT=$(openclaw message send --channel discord --target "$CHANNEL" --message "$BOARD" 2>&1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Posted board: $RESULT" >> "$LOG"

# Extract message ID from result (try to parse JSON output)
NEW_MSG_ID=$(echo "$RESULT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('result', {}).get('messageId', ''))
except:
    # fallback: try to find ID pattern
    import re
    m = re.search(r'\"messageId\":\s*\"(\d+)\"', sys.stdin.read())
    print(m.group(1) if m else '')
" 2>/dev/null) || true

# Pin new board
if [ -n "$NEW_MSG_ID" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pinning new: $NEW_MSG_ID" >> "$LOG"
    openclaw message pin --channel discord --target "$CHANNEL" --message-id "$NEW_MSG_ID" >> "$LOG" 2>&1 || true

    # Save state
    python3 -c "
import json
state = {'last_pin_message_id': '$NEW_MSG_ID', 'last_refresh': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'}
open('$STATE', 'w').write(json.dumps(state, indent=2))
" 2>/dev/null || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pin rotated successfully." >> "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: Could not extract message ID for pinning." >> "$LOG"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Board refresh done." >> "$LOG"
