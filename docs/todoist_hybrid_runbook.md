# Todoist Hybrid Runbook (MVP)

> Last verified: 2026-02-12 — all commands pass end-to-end.

## Quick Start

```bash
cd /Users/ellisbot/.openclaw/workspace
python3 scripts/todoist_bridge.py <command>
```

## Commands

### Test Auth
```bash
python3 scripts/todoist_bridge.py test
# ✅ Auth OK (HTTP 200). 5 projects: ...
```

### List Tasks (Business Ops project)
```bash
python3 scripts/todoist_bridge.py list
python3 scripts/todoist_bridge.py list --filter "today | overdue"
```

### Add Task
```bash
python3 scripts/todoist_bridge.py add --content "Your task here"
python3 scripts/todoist_bridge.py add --content "Marco's task" --section Marco
python3 scripts/todoist_bridge.py add --content "Due tomorrow" --section Ellis --due-string "tomorrow" --priority 2
```

Sections: `Ellis`, `Marco`, `Blocked`, `Recurring`

### Complete Task
```bash
python3 scripts/todoist_bridge.py close --task-id <TASK_ID>
```

### Sync tracker → Todoist (idempotent)
```bash
python3 scripts/todoist_bridge.py sync
```
Reads `task_tracker.md`, creates only new tasks in Todoist Business Ops → Ellis section. Safe to run repeatedly.

### Setup Project (already done)
```bash
python3 scripts/todoist_bridge.py setup --project-name "Business Ops"
```

## Token Resolution

The script resolves the Todoist API token in this order:

1. **`TODOIST_TOKEN` env var** — fastest, no 1Password dependency
2. **`~/.todoist_token` file** — cached, persists across sessions
3. **1Password CLI** — `op read "op://Private/Todoist Token/notesPlain"`

## When Auth Breaks (op hangs)

The 1Password CLI (`op`) sometimes hangs waiting for desktop app unlock. Fix:

### Option A: Re-cache token via tmux
```bash
tmux new-session -d -s opauth
tmux send-keys -t opauth "op item get 'Todoist Token' --fields notesPlain > ~/.todoist_token" Enter
# Wait for 1Password desktop prompt, approve, then:
chmod 600 ~/.todoist_token
```

### Option B: Set env var directly
```bash
export TODOIST_TOKEN="$(cat ~/.todoist_token)"
python3 scripts/todoist_bridge.py test
```

### Option C: Manual token refresh
1. Open 1Password app → find "Todoist Token" → copy notesPlain value
2. `echo "<token>" > ~/.todoist_token && chmod 600 ~/.todoist_token`

## Architecture

```
task_tracker.md ──sync──▶ Todoist "Business Ops" project
                           ├── Ellis (section)
                           ├── Marco (section)
                           ├── Blocked (section)
                           └── Recurring (section)
```

- **Project ID:** `6g246PHRgJxCFwgC`
- **Script:** `scripts/todoist_bridge.py`
- **Token cache:** `~/.todoist_token` (chmod 600)
- **No external dependencies** — uses only Python stdlib (`urllib`, `json`, `subprocess`)

## Key IDs

| Entity | ID |
|--------|-----|
| Business Ops project | `6g246PHRgJxCFwgC` |
| Ellis section | `6g246PcGRvGv7HWC` |
| Marco section | `6g246PhcFf67xGwC` |
| Blocked section | `6g246Pjqp8jGCjXC` |
| Recurring section | `6g246Q2vpQXq9HMj` |
