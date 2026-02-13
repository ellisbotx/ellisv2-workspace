#!/usr/bin/env python3
"""Poll Todoist for changes and generate event messages for #tasks.

Runs every 5 minutes. Detects:
- New tasks added
- Tasks completed (removed from open list)
- Tasks updated (content, section, due date, priority changed)

Outputs event message to stdout if changes detected.
Exit code: 0 = changes found, 1 = no changes, 2 = error.

State file: data/todoist_event_state.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import from existing todoist_bridge
sys.path.insert(0, str(Path(__file__).parent))
from todoist_bridge import api, _results, SECTION_MAP, DEFAULT_PROJECT_ID

WORKSPACE = Path(__file__).resolve().parent.parent
STATE_FILE = WORKSPACE / "data" / "todoist_event_state.json"

# Reverse section map: id -> name
SECTION_NAMES = {v: k for k, v in SECTION_MAP.items()}


def load_state():
    """Load last-known state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return {"last_poll": None, "tasks": {}}


def save_state(state):
    """Save state to file atomically via tmp rename."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    tmp.rename(STATE_FILE)


def fetch_current_tasks():
    """Fetch all open tasks from Business Ops project."""
    _, data = api("GET", f"/tasks?project_id={DEFAULT_PROJECT_ID}")
    tasks = _results(data)
    result = {}
    for t in tasks:
        tid = str(t.get("id", ""))
        due_info = t.get("due") or {}
        result[tid] = {
            "content": t.get("content", ""),
            "section_id": t.get("section_id", ""),
            "due": due_info.get("date", "") if isinstance(due_info, dict) else "",
            "priority": t.get("priority", 1),
        }
    return result


def detect_changes(old_tasks, new_tasks):
    """Compare old and new task states. Returns (added, completed, updated)."""
    old_ids = set(old_tasks.keys())
    new_ids = set(new_tasks.keys())

    added = []
    for tid in sorted(new_ids - old_ids):
        t = new_tasks[tid]
        sec = SECTION_NAMES.get(t["section_id"], "")
        added.append({
            "id": tid,
            "content": t["content"],
            "section": sec,
            "due": t["due"],
        })

    completed = []
    for tid in sorted(old_ids - new_ids):
        t = old_tasks[tid]
        sec = SECTION_NAMES.get(t["section_id"], "")
        completed.append({
            "id": tid,
            "content": t["content"],
            "section": sec,
        })

    updated = []
    for tid in sorted(old_ids & new_ids):
        old = old_tasks[tid]
        new = new_tasks[tid]
        changes = []
        if old["content"] != new["content"]:
            changes.append(f"renamed")
        if old["section_id"] != new["section_id"]:
            old_sec = SECTION_NAMES.get(old["section_id"], "?")
            new_sec = SECTION_NAMES.get(new["section_id"], "?")
            changes.append(f"moved: {old_sec} → {new_sec}")
        if old["due"] != new["due"]:
            changes.append(f"due: {old['due'] or 'none'} → {new['due'] or 'none'}")
        if old["priority"] != new["priority"]:
            changes.append(f"priority: P{old['priority']} → P{new['priority']}")
        if changes:
            updated.append({
                "id": tid,
                "content": new["content"],
                "section": SECTION_NAMES.get(new["section_id"], ""),
                "changes": changes,
            })

    return added, completed, updated


def format_event_message(added, completed, updated):
    """Format a bundled event message for Discord (under 2000 chars)."""
    lines = ["📋 **Todoist Update**"]
    now_str = datetime.now().strftime("%I:%M %p")
    lines.append(f"*{now_str} CST*\n")

    if completed:
        lines.append("**✅ Completed:**")
        for t in completed[:10]:
            sec = f" [{t['section']}]" if t["section"] else ""
            lines.append(f"• ~~{t['content'][:100]}~~{sec}")
        lines.append("")

    if added:
        lines.append("**➕ Added:**")
        for t in added[:10]:
            sec = f" [{t['section']}]" if t["section"] else ""
            due = f" (due: {t['due']})" if t["due"] else ""
            lines.append(f"• {t['content'][:100]}{sec}{due}")
        lines.append("")

    if updated:
        lines.append("**✏️ Updated:**")
        for t in updated[:10]:
            change_str = ", ".join(t["changes"])
            lines.append(f"• {t['content'][:80]} — {change_str}")
        lines.append("")

    total = len(added) + len(completed) + len(updated)
    lines.append(f"*{total} change{'s' if total != 1 else ''}*")

    msg = "\n".join(lines)
    if len(msg) > 1950:
        msg = msg[:1940] + "\n…(truncated)"
    return msg


def main():
    state = load_state()
    old_tasks = state.get("tasks", {})

    try:
        current_tasks = fetch_current_tasks()
    except Exception as e:
        print(f"❌ Todoist poll error: {e}", file=sys.stderr)
        sys.exit(2)

    # First run: initialize state, don't report everything as new
    if not old_tasks and not state.get("last_poll"):
        save_state({
            "last_poll": datetime.now(timezone.utc).isoformat(),
            "tasks": current_tasks,
        })
        print(f"[init] State initialized with {len(current_tasks)} tasks. No events on first run.")
        sys.exit(1)

    # Detect changes
    added, completed, updated = detect_changes(old_tasks, current_tasks)

    if not added and not completed and not updated:
        state["last_poll"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        sys.exit(1)  # No changes

    # Output the event message
    message = format_event_message(added, completed, updated)
    print(message)

    # Save new state
    save_state({
        "last_poll": datetime.now(timezone.utc).isoformat(),
        "tasks": current_tasks,
    })

    sys.exit(0)


if __name__ == "__main__":
    main()
