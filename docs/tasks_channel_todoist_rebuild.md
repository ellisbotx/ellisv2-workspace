# #tasks Channel — Todoist-First Rebuild

**Date:** 2026-02-12  
**Status:** Live (MVP)  
**Channel:** #tasks (`1470181819067531500`)  
**Source of truth:** Todoist → Business Ops project (`6g246PHRgJxCFwgC`)

---

## Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Todoist    │◄──►│ todoist_bridge.py │    │ #tasks channel  │
│  (source of  │    │  (API layer)      │    │ (visibility     │
│   truth)     │    └────────┬─────────┘    │  layer only)    │
└─────────────┘             │               └────────▲────────┘
                            │                        │
                ┌───────────┴───────────┐            │
                │                       │            │
        ┌───────▼───────┐     ┌─────────▼──────┐     │
        │ poll_events.py│     │summary_board.py│     │
        │ (every 5 min) │     │ (every hour)   │     │
        └───────┬───────┘     └────────┬───────┘     │
                │                      │             │
                └──────────┬───────────┘             │
                           │                         │
                    ┌──────▼──────┐                  │
                    │ cron shells │──────────────────►│
                    │ (post only  │                   │
                    │  on change) │                   │
                    └─────────────┘
```

### Key Principles
1. **Todoist is the source of truth** — all task CRUD happens in Todoist
2. **#tasks is a read-only visibility layer** — shows events + summary board
3. **Event-driven, not polling-driven** — posts only when changes are detected
4. **No spam** — silent when nothing changes; bundles multiple changes into one post
5. **Idempotent** — safe to re-run; state file tracks last-known snapshot

---

## Components

### 1. `scripts/todoist_poll_events.py` — Change Detection (every 5 min)
- Fetches current open tasks from Todoist Business Ops project
- Compares against `data/todoist_event_state.json` (last-known state)
- Detects: **added** (new IDs), **completed** (missing IDs), **updated** (content/section/due/priority changed)
- First run: initializes state silently (no "everything is new" spam)
- Exit codes: `0` = changes found (message on stdout), `1` = no changes, `2` = error

### 2. `scripts/todoist_summary_board.py` — Summary Board (every hour)
- Fetches all open tasks, categorizes by urgency:
  - 🔴 **Urgent** — priority ≥ 3 or due within 3 days
  - 🟢 **Ellis** — tasks in Ellis section
  - 🟡 **Marco** — tasks in Marco section
  - 🔄 **Recurring** — tasks in Recurring section
  - 🚫 **Blocked** — tasks in Blocked section
- Outputs formatted board (kept under 2000 chars for Discord)

### 3. `scripts/todoist_poll_cron.sh` — Poll Wrapper
- Runs `todoist_poll_events.py`
- Posts to #tasks via `openclaw message send` ONLY if changes detected
- Logs to `logs/todoist_poll.log`

### 4. `scripts/todoist_board_cron.sh` — Board Wrapper
- Runs `todoist_summary_board.py`
- Unpins old board, posts new board, pins it
- Saves message ID to `data/todoist_board_state.json` for next pin rotation
- Logs to `logs/todoist_board.log`

### 5. State Files
- `data/todoist_event_state.json` — last-known task IDs + content for diff detection
- `data/todoist_board_state.json` — last pinned message ID for pin rotation

---

## Scheduling

| Job | Frequency | Mechanism | LaunchAgent |
|-----|-----------|-----------|-------------|
| Event poll | Every 5 min (300s) | LaunchAgent | `com.openclaw.todoist-poll` |
| Board refresh | Every hour (3600s) | LaunchAgent | `com.openclaw.todoist-board` |

Both LaunchAgents have `RunAtLoad: false` to avoid startup spam.

---

## Manual Commands

```bash
# Test Todoist API auth
python3 scripts/todoist_bridge.py test

# Run event poll manually (outputs message if changes, silent if none)
python3 scripts/todoist_poll_events.py

# Generate summary board
python3 scripts/todoist_summary_board.py

# Add a task via CLI
python3 scripts/todoist_bridge.py add --content "New task" --section Ellis

# List all open tasks
python3 scripts/todoist_bridge.py list

# Complete a task
python3 scripts/todoist_bridge.py close --task-id <ID>

# Force-run the cron wrappers
bash scripts/todoist_poll_cron.sh
bash scripts/todoist_board_cron.sh
```

---

## Anti-Spam Guarantees

1. **No-change silence:** Poll script exits `1` with no output when nothing changed → wrapper doesn't post
2. **Bundled events:** Multiple adds/completes/updates in one 5-min window → single message
3. **First-run safety:** State initializes silently on first ever run (no "20 tasks added" flood)
4. **Board capping:** Max 8 items per category shown; overflow indicated with "+N more"
5. **Message length:** Hard cap at 1950 chars; truncated if exceeded

---

## Rollback

### Disable polling + board refresh:
```bash
launchctl unload ~/Library/LaunchAgents/com.openclaw.todoist-poll.plist
launchctl unload ~/Library/LaunchAgents/com.openclaw.todoist-board.plist
```

### Re-enable:
```bash
launchctl load ~/Library/LaunchAgents/com.openclaw.todoist-poll.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.todoist-board.plist
```

### Remove completely:
```bash
launchctl unload ~/Library/LaunchAgents/com.openclaw.todoist-poll.plist
launchctl unload ~/Library/LaunchAgents/com.openclaw.todoist-board.plist
rm ~/Library/LaunchAgents/com.openclaw.todoist-poll.plist
rm ~/Library/LaunchAgents/com.openclaw.todoist-board.plist
```

### Reset state (re-initializes from current Todoist snapshot):
```bash
rm data/todoist_event_state.json
rm data/todoist_board_state.json
```

---

## Todoist Project Structure

| Section | ID | Purpose |
|---------|-----|---------|
| Ellis | `6g246PcGRvGv7HWC` | Tasks Ellis handles autonomously |
| Marco | `6g246PhcFf67xGwC` | Tasks requiring Marco's action |
| Blocked | `6g246Pjqp8jGCjXC` | Tasks blocked on external deps |
| Recurring | `6g246Q2vpQXq9HMj` | Recurring/scheduled tasks |

---

## Future Improvements

- [ ] Todoist webhook integration (instant events instead of 5-min polling)
- [ ] Completion activity log (Todoist Sync API `completed/get_all`)
- [ ] Two-way sync: commands in #tasks channel → Todoist actions
- [ ] Priority emoji mapping in board (P1-P4 visual indicators)
- [ ] Category-specific alerts (urgent tasks → #alerts)
