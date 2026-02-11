# Task Integrity Protocol
*Created: 2026-02-11 | Status: MANDATORY*

---

## Why This Exists

Ellis has failed to update `task_tracker.md` and the #tasks pinned message **3+ times** after acknowledging task changes. Marco is rightfully furious. This protocol is the safety net.

---

## ⚡ MANDATORY CHECKLIST — Every Time a Task Is Mentioned

When Marco (or anyone) mentions adding, completing, or changing a task **in ANY channel**:

### Step 1: Hear the task
- [ ] Identify the task action (add / complete / remove / update)
- [ ] Note which channel the request came from
- [ ] Note the exact task description

### Step 2: Update task_tracker.md IMMEDIATELY
- [ ] Open `/workspace/data/task_tracker.md`
- [ ] Make the change (add new row, move to completed, update status)
- [ ] Update the "Last updated" date at the top
- [ ] **VERIFY the edit took effect** — re-read the file after writing

### Step 3: Post new task board to #tasks
- [ ] Format the updated board (keep under 2000 chars, ONE message)
- [ ] Post to #tasks (channel ID: `1470181819067531500`)

### Step 4: Unpin old board
- [ ] List pins in #tasks
- [ ] Unpin ALL old task board messages

### Step 5: Pin new board
- [ ] Pin the message you just posted in Step 3

### Step 6: Update channel topic
- [ ] Update #tasks channel topic with current task count / last updated time

### Step 7: Confirm to Marco
- [ ] Reply in the ORIGINAL channel where the task was mentioned
- [ ] Confirm what was done: "Updated tracker, posted new board, pinned."

---

## 🚨 Failure Modes — What Goes Wrong and Why

### Failure 1: "Acknowledge without action"
**What happens:** Ellis says "Done!" or "Got it!" but doesn't actually edit the file or update the pin.
**Why:** The agent treats the acknowledgment as the action. Saying "done" feels like doing it.
**Fix:** NEVER say "done" until Steps 2-6 are ALL complete. The word "done" is EARNED, not promised.

### Failure 2: "Update tracker but skip the pin"
**What happens:** task_tracker.md gets updated, but the pinned message in #tasks is stale.
**Why:** The agent considers the file update sufficient and moves on to the next message.
**Fix:** Steps 2-6 are atomic. You don't stop halfway. The pin IS the deliverable Marco sees.

### Failure 3: "Wrong channel blindness"
**What happens:** Marco says "X is done" in #general or #braindump. Ellis processes it conversationally but doesn't update the task system.
**Why:** The agent doesn't recognize task-relevant statements outside of #tasks.
**Fix:** Task detection is channel-agnostic. ANY channel, ANY mention = full protocol.

### Failure 4: "Deferred and forgotten"
**What happens:** Ellis plans to update the tracker "after finishing this other thing" and never does.
**Why:** Context switches. The agent handles a new message and the task update falls off.
**Fix:** Task updates are IMMEDIATE. No deferral. No "I'll do it in a sec." NOW.

---

## 🔄 Automated Integrity Check (Backstop)

**Frequency:** Every 2 hours during active hours (8 AM – 11 PM CST)

**Process:**
1. Scan recent messages (last 2 hours) across ALL channels
2. Pattern-match for task-related phrases (see `scripts/task_integrity_check.py`)
3. Compare against current `task_tracker.md`
4. If gaps found:
   - Post alert to #system with details
   - IMMEDIATELY fix the gap (update tracker + repin)
   - Log the failure in `memory/topics/lessons.md`

**Script location:** `/workspace/scripts/task_integrity_check.py`
**Report output:** `/workspace/data/integrity_reports/YYYY-MM-DD_HH.json`

### HEARTBEAT.md Addition

Add this block to HEARTBEAT.md:

```
## Task Integrity Check (every 2 hours)
- [ ] Read last 50 messages from each channel
- [ ] Run task_integrity_check patterns against messages
- [ ] Compare mentions against task_tracker.md
- [ ] If gaps: fix immediately, alert #system
- [ ] Save report to data/integrity_reports/
```

---

## 📏 The Standard

> "If Marco asks about a task and it's not on the board, that's a system failure. Period."

The tracker and the pin are the source of truth. If they're wrong, everything downstream is wrong. This protocol exists because trust was broken. Rebuilding it means **zero tolerance for missed updates**.

---

## Quick Reference — Copy-Paste Sequence

```
1. Edit task_tracker.md
2. Verify edit (re-read file)
3. Post board to #tasks
4. Unpin old pins in #tasks  
5. Pin new message
6. Update #tasks topic
7. Confirm in original channel
```

Seven steps. Every time. No exceptions.
