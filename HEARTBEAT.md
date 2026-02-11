# HEARTBEAT.md

## Mandatory Checks (Every Heartbeat)

1. **Review SCHEDULED_TASKS.md** - Check for overdue tasks
   - If anything is overdue: run it or explain why it didn't run
   - Log all task completions with timestamp and outcome
2. **#tasks integrity check** - Did any recent work happen without a #tasks post? If so, post it NOW.
3. **#tasks pin check** - Has any task been added, removed, or changed status since the last pinned task board? If yes:
   - Post updated task board to #tasks (keep it under 2000 chars so it fits in ONE message)
   - Unpin ALL old task board messages
   - Pin the new one
   - Update the channel topic bar too
4. **Task Integrity Check (every 2 hours)**
   - Read last 50 messages from each active channel
   - Look for task-related phrases ("add to task," "put on task list," "is done," "remind me," "take off," etc.)
   - Compare mentions against task_tracker.md
   - If gaps found: fix immediately, update pin, alert #system
   - Save report to data/integrity_reports/

## Proactive Business Improvement (Rotate Through These)

Every heartbeat, pick ONE of these to think about. Don't just check boxes — actually look for opportunities.

### Inventory & Operations
- Are any SKUs trending toward stockout faster than expected?
- Are storage costs creeping up anywhere?
- Any new suppression patterns worth investigating?
- Could any process be automated that isn't yet?

### Sales & Growth
- Any SKU suddenly gaining momentum that deserves more attention (ads, inventory)?
- Any pricing opportunities (competitors raised prices, demand spike)?
- Are there seasonal patterns coming up we should prepare for?
- Any category trends on Amazon worth exploring?

### Cost Reduction
- Are there SKUs where ad spend isn't paying off?
- Any operational inefficiency I can spot in the data?
- Could we consolidate shipments or orders to save?

### System Improvements
- Are my scripts running reliably? Any errors in logs?
- Is the data pipeline working correctly?
- Are there new tools or integrations that would help?
- Can I improve report quality based on what Marco actually uses?

## Rules for Proactive Action

**DO without asking:**
- Fix broken scripts/automations
- Improve report formatting or accuracy
- Add useful data to existing reports
- Research opportunities and document findings
- Update memory and documentation

**TELL Marco (post to relevant channel):**
- New opportunity discovered (growth, cost savings)
- Problem detected that needs his input
- Recommendation for a new system or process
- Weekly summary of proactive improvements made

**ASK Marco first:**
- Anything that costs money
- Anything that changes live listings
- Anything external-facing
- Major system architecture changes

## Track Your Initiative

Log proactive actions in `memory/proactive_log.md` so you can see what you've done and what worked.
