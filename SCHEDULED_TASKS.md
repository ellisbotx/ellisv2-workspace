# SCHEDULED_TASKS.md

**Purpose:** Track all scheduled tasks, log completions, and catch anything overdue.

**Heartbeat Protocol:** On each heartbeat, review this file. If anything is overdue, run it or explain why it didn't run.

---

## Active Scheduled Tasks

### Daily ASIN Suppression Check
- **Frequency:** Daily at 1:00 AM CST
- **Mechanism:** Cron job (`05b73d8d-df85-4893-bf28-7f96fdb654a2`)
- **Script:** `/Users/ellisbot/.openclaw/workspace/scripts/asin_checker.py`
- **Output:** `/Users/ellisbot/.openclaw/workspace/data/suppression_tracker.csv`
- **Reporting:** Posts to #reports (summary) + #alerts (if suppressions found)
- **Next run:** Tonight, Feb 6, 2026 @ 1:00 AM CST
- **Last completed:** See log below

### Weekly Memory Consolidation
- **Frequency:** Sundays at 8:00 PM CST
- **Mechanism:** Cron job (`4da85d88-020c-49f9-b5de-a6da7c3061c4`)
- **Action:** Review last 7 days of memory/*.md files, suggest MEMORY.md updates
- **Reporting:** Posts to #system channel
- **Next run:** Sunday, Feb 9, 2026 @ 8:00 PM CST
- **Last completed:** See log below

### Heartbeat Proactive Checks
- **Frequency:** Hourly (main agent only)
- **Mechanism:** OpenClaw heartbeat system
- **Action:** Review HEARTBEAT.md (currently empty), check for overdue scheduled tasks
- **Reporting:** Posts to relevant channels if alerts needed, otherwise HEARTBEAT_OK
- **Next run:** Every hour
- **Last completed:** See log below

---

## Completion Log

### Format
```
YYYY-MM-DD HH:MM CST | [TASK NAME] | Status | Outcome
```

### Recent Completions

2026-02-06 01:07 CST | Daily ASIN Suppression Check | FAILED | 163/166 errors (503 Service Unavailable from Amazon API) - only 3 ASINs checked successfully
2026-02-05 16:26 CST | OpenClaw Update (Ad-hoc) | SUCCESS | Updated from 2026.2.2-3 to 2026.2.3-1, gateway restarted cleanly
2026-02-05 01:09 CST | Daily ASIN Suppression Check | SUCCESS | Checked 166 ASINs, results saved to suppression_tracker.csv

---

## Overdue Tasks

*None currently.*

---

## Notes

- Tasks are considered **overdue** if they haven't run within 2x their expected frequency
- Daily tasks: overdue after 48 hours
- Weekly tasks: overdue after 14 days
- Hourly tasks: overdue after 2 hours (for critical checks only)

- When logging completions, include:
  - Timestamp (CST)
  - Task name
  - Status (SUCCESS, FAILED, SKIPPED)
  - Brief outcome (what happened, any alerts sent, errors encountered)

- This file is reviewed on every heartbeat to ensure nothing falls through the cracks
