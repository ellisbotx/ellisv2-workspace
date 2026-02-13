#!/usr/bin/env python3
"""Generate a clean Todoist summary board for #tasks channel.

Categories:
  🔴 Urgent — priority >= 3 or due within 3 days
  🟢 Ellis (Pending) — tasks in Ellis section
  🟡 Marco (Action Needed) — tasks in Marco section
  🔄 Recurring — tasks in Recurring section
  🚫 Blocked — tasks in Blocked section

Outputs formatted board to stdout (under 2000 chars for Discord).
Exit code: 0 = success, 2 = error.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from todoist_bridge import api, _results, SECTION_MAP, DEFAULT_PROJECT_ID

WORKSPACE = Path(__file__).resolve().parent.parent
BOARD_STATE_FILE = WORKSPACE / "data" / "todoist_board_state.json"

SECTION_NAMES = {v: k for k, v in SECTION_MAP.items()}


def load_board_state():
    if BOARD_STATE_FILE.exists():
        try:
            return json.loads(BOARD_STATE_FILE.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return {"last_pin_message_id": None, "last_refresh": None}


def save_board_state(state):
    BOARD_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = BOARD_STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.rename(BOARD_STATE_FILE)


def fetch_tasks():
    _, data = api("GET", f"/tasks?project_id={DEFAULT_PROJECT_ID}")
    return _results(data)


def categorize_tasks(tasks):
    """Sort tasks into urgency buckets. Returns (urgent, ellis, marco, recurring, blocked)."""
    now = datetime.now().date()
    urgent_cutoff = now + timedelta(days=3)

    urgent, ellis, marco, recurring, blocked = [], [], [], [], []

    for t in tasks:
        content = t.get("content", "")[:90]
        section_id = t.get("section_id", "")
        section_name = SECTION_NAMES.get(section_id, "")
        priority = t.get("priority", 1)
        due_info = t.get("due") or {}
        due_date = due_info.get("date", "") if isinstance(due_info, dict) else ""

        due_str = f" `{due_date}`" if due_date else ""
        is_urgent = priority >= 3

        if due_date:
            try:
                d = datetime.strptime(due_date[:10], "%Y-%m-%d").date()
                if d <= urgent_cutoff:
                    is_urgent = True
            except ValueError:
                pass

        entry = f"{content}{due_str}"

        if section_name == "Blocked":
            blocked.append(entry)
        elif section_name == "Recurring":
            recurring.append(entry)
        elif is_urgent:
            urgent.append(entry)
        elif section_name == "Marco":
            marco.append(entry)
        else:
            ellis.append(entry)

    return urgent, ellis, marco, recurring, blocked


def format_board(urgent, ellis, marco, recurring, blocked):
    """Format the board as a Discord message (<2000 chars)."""
    now_str = datetime.now().strftime("%b %d, %I:%M %p")
    total = len(urgent) + len(ellis) + len(marco) + len(recurring) + len(blocked)

    lines = [f"📌 **Task Board** — {now_str} CST"]
    lines.append(f"*{total} open tasks in Todoist*\n")

    if urgent:
        lines.append("🔴 **Urgent / Due Soon:**")
        for t in urgent[:8]:
            lines.append(f"• {t}")
        if len(urgent) > 8:
            lines.append(f"  *(+{len(urgent)-8} more)*")
        lines.append("")

    if ellis:
        lines.append("🟢 **Ellis (Pending):**")
        for t in ellis[:8]:
            lines.append(f"• {t}")
        if len(ellis) > 8:
            lines.append(f"  *(+{len(ellis)-8} more)*")
        lines.append("")

    if marco:
        lines.append("🟡 **Marco (Action Needed):**")
        for t in marco[:8]:
            lines.append(f"• {t}")
        if len(marco) > 8:
            lines.append(f"  *(+{len(marco)-8} more)*")
        lines.append("")

    if recurring:
        lines.append("🔄 **Recurring:**")
        for t in recurring[:5]:
            lines.append(f"• {t}")
        if len(recurring) > 5:
            lines.append(f"  *(+{len(recurring)-5} more)*")
        lines.append("")

    if blocked:
        lines.append("🚫 **Blocked:**")
        for t in blocked[:5]:
            lines.append(f"• {t}")
        if len(blocked) > 5:
            lines.append(f"  *(+{len(blocked)-5} more)*")
        lines.append("")

    lines.append("*Auto-generated from Todoist • Updates hourly*")

    msg = "\n".join(lines)
    if len(msg) > 1950:
        msg = msg[:1940] + "\n…(truncated)"
    return msg


def main():
    try:
        tasks = fetch_tasks()
    except Exception as e:
        print(f"❌ Failed to fetch tasks: {e}", file=sys.stderr)
        sys.exit(2)

    urgent, ellis, marco, recurring, blocked = categorize_tasks(tasks)
    board = format_board(urgent, ellis, marco, recurring, blocked)
    print(board)
    sys.exit(0)


if __name__ == "__main__":
    main()
