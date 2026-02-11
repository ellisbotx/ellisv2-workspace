#!/usr/bin/env bash
set -euo pipefail

BASE="/Users/ellisbot/.openclaw/workspace"
TOPICS_DIR="$BASE/memory/topics"
HEALTH_FILE="$BASE/memory/health.json"
QMD="/Users/ellisbot/.bun/bin/qmd"
TODAY=$(date +%Y-%m-%d)
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

TOPIC_FILES=("business.md" "preferences.md" "systems.md" "agents.md" "lessons.md")
CRITICAL=0
GAPS=()
TOTAL_LINES=0

echo "=== Memory Health Check ==="
echo "Time: $NOW"
echo ""

# ── 1. Check MEMORY.md index ──
if [[ ! -f "$BASE/MEMORY.md" ]]; then
  GAPS+=("MEMORY.md index missing")
  CRITICAL=1
  echo "❌ MEMORY.md index missing"
else
  echo "✅ MEMORY.md index exists"
fi

# ── 2. Check topic files ──
echo ""
echo "Topic files:"
TOPIC_JSON="{"
for f in "${TOPIC_FILES[@]}"; do
  path="$TOPICS_DIR/$f"
  if [[ -f "$path" ]]; then
    lines=$(wc -l < "$path" | tr -d ' ')
    exists=true
    if (( lines <= 5 )); then
      GAPS+=("$f has only $lines lines (expected >5)")
      CRITICAL=1
      echo "  ⚠️  $f ($lines lines — TOO THIN)"
    else
      echo "  ✅ $f ($lines lines)"
    fi
  else
    lines=0
    exists=false
    GAPS+=("$f missing")
    CRITICAL=1
    echo "  ❌ $f MISSING"
  fi
  TOTAL_LINES=$((TOTAL_LINES + lines))
  TOPIC_JSON+="\"$f\":{\"exists\":$exists,\"lines\":$lines},"
done
TOPIC_JSON="${TOPIC_JSON%,}}"

# Count MEMORY.md lines
if [[ -f "$BASE/MEMORY.md" ]]; then
  TOTAL_LINES=$((TOTAL_LINES + $(wc -l < "$BASE/MEMORY.md" | tr -d ' ')))
fi

# ── 3. Check today's daily log ──
echo ""
DAILY_LOG="$BASE/memory/$TODAY.md"
if [[ -f "$DAILY_LOG" ]]; then
  DAILY_TODAY=true
  daily_lines=$(wc -l < "$DAILY_LOG" | tr -d ' ')
  TOTAL_LINES=$((TOTAL_LINES + daily_lines))
  echo "✅ Daily log ($TODAY): $daily_lines lines"
else
  DAILY_TODAY=false
  GAPS+=("No daily log for $TODAY")
  echo "❌ No daily log for $TODAY"
fi

# ── 4. Count all daily logs ──
daily_count=$(find "$BASE/memory" -maxdepth 1 -name "202*.md" | wc -l | tr -d ' ')
echo "📊 Total daily logs: $daily_count"

# ── 5. QMD Index Health ──
echo ""
echo "QMD Search Index:"
if [[ -x "$QMD" ]]; then
  # Get index stats
  qmd_status=$("$QMD" status 2>&1) || true
  indexed_files=$(echo "$qmd_status" | grep "Total:" | grep -oE '[0-9]+' | head -1 || echo "0")
  vectors=$(echo "$qmd_status" | grep "Vectors:" | grep -oE '[0-9]+' | head -1 || echo "0")
  
  echo "  📁 Files indexed: ${indexed_files:-0}"
  echo "  🔢 Vectors: ${vectors:-0}"
  
  if [[ "${indexed_files:-0}" -lt 10 ]]; then
    GAPS+=("QMD index has only ${indexed_files:-0} files (expected 15+)")
    CRITICAL=1
    echo "  ❌ Index too small — triggering re-index..."
    cd "$BASE" && "$QMD" update 2>&1 | tail -3
    "$QMD" embed 2>&1 | tail -3
    echo "  ✅ Re-index complete"
  fi
  
  # Test a known search
  search_result=$("$QMD" search "Card Plug margin" -n 1 2>&1) || true
  if echo "$search_result" | grep -qi "card plug\|margin\|40%"; then
    SEARCH_PASS=true
    echo "  ✅ Search test passed (found Card Plug margin data)"
  else
    SEARCH_PASS=false
    GAPS+=("Search test failed — 'Card Plug margin' returned no relevant results")
    CRITICAL=1
    echo "  ❌ Search test FAILED"
  fi
else
  GAPS+=("qmd binary not found at $QMD")
  CRITICAL=1
  SEARCH_PASS=false
  echo "  ❌ qmd binary not found"
fi

# ── 6. Check for stale topic files (not updated in 14+ days) ──
echo ""
echo "Freshness check:"
for f in "${TOPIC_FILES[@]}"; do
  path="$TOPICS_DIR/$f"
  if [[ -f "$path" ]]; then
    # Get file age in days
    if [[ "$(uname)" == "Darwin" ]]; then
      file_mtime=$(stat -f %m "$path")
    else
      file_mtime=$(stat -c %Y "$path")
    fi
    now_epoch=$(date +%s)
    age_days=$(( (now_epoch - file_mtime) / 86400 ))
    if (( age_days > 14 )); then
      GAPS+=("$f not updated in ${age_days} days")
      echo "  ⚠️  $f — last updated ${age_days} days ago (stale)"
    else
      echo "  ✅ $f — updated ${age_days} day(s) ago"
    fi
  fi
done

# ── 7. Build gaps JSON ──
GAPS_JSON="["
for g in "${GAPS[@]+"${GAPS[@]}"}"; do
  GAPS_JSON+="\"$(echo "$g" | sed 's/"/\\"/g')\","
done
GAPS_JSON="${GAPS_JSON%,}]"

# ── 8. Write health.json ──
cat > "$HEALTH_FILE" <<EOF
{
  "lastCheck": "$NOW",
  "topicFiles": $TOPIC_JSON,
  "dailyLogToday": $DAILY_TODAY,
  "dailyLogCount": $daily_count,
  "totalMemoryLines": $TOTAL_LINES,
  "qmdIndexedFiles": ${indexed_files:-0},
  "qmdVectors": ${vectors:-0},
  "searchTestPassed": ${SEARCH_PASS:-false},
  "lastConsolidation": null,
  "gaps": $GAPS_JSON
}
EOF

# ── Summary ──
echo ""
echo "════════════════════════════"
echo "Total memory lines: $TOTAL_LINES"
echo "QMD indexed: ${indexed_files:-0} files, ${vectors:-0} vectors"
echo "Search test: $([ "${SEARCH_PASS:-false}" = true ] && echo '✅ PASS' || echo '❌ FAIL')"
if (( ${#GAPS[@]} > 0 )); then
  echo "⚠️  ${#GAPS[@]} gap(s) found:"
  for g in "${GAPS[@]}"; do
    echo "  - $g"
  done
else
  echo "✅ No gaps found"
fi
echo "Results written to $HEALTH_FILE"

exit $CRITICAL
