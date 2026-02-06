# HEARTBEAT.md

## Mandatory Checks (Every Heartbeat)

1. **Review SCHEDULED_TASKS.md** - Check for overdue tasks
   - If anything is overdue: run it or explain why it didn't run
   - Log all task completions with timestamp and outcome

## Optional Periodic Checks

# Keep tasks below empty (or with only comments) to skip optional heartbeat actions.
# Add tasks when you want the agent to check something periodically.

# ASIN checking is now handled by the script-based cron job at 1 AM CST daily.
# Script: /Users/ellisbot/.openclaw/workspace/scripts/asin_checker.py
# Results: /Users/ellisbot/.openclaw/workspace/data/suppression_tracker.csv
