#!/usr/bin/env python3
"""Todoist bridge — MVP for OpenClaw workspace.

Token resolution (in order):
  1. TODOIST_TOKEN env var (fastest, no op dependency)
  2. ~/.todoist_token cache file
  3. 1Password CLI: op read "op://Private/Todoist Token/notesPlain"

Commands:
  test                                - verify auth and list projects
  setup --project-name ...            - ensure project + standard sections exist
  add --content ... [--section ...]   - create task (optional --project-id, --due-string, --priority, --section)
  list [--filter ...] [--project-id]  - list tasks (default: all in Business Ops)
  close --task-id ...                 - complete task
  sync                                - sync local task_tracker.md → Todoist (idempotent)
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import urllib.error

ONEPASSWORD_ITEM_REF = os.getenv("TODOIST_TOKEN_OP_REF", "op://Private/Todoist Token/notesPlain")
TODOIST_API_BASE = "https://api.todoist.com/api/v1"
TOKEN_CACHE = pathlib.Path.home() / ".todoist_token"
WORKSPACE = pathlib.Path(__file__).resolve().parent.parent
TASK_TRACKER = WORKSPACE / "data" / "task_tracker.md"

# Canonical Business Ops project (first one with sections)
DEFAULT_PROJECT_ID = "6g246PHRgJxCFwgC"
SECTION_MAP = {
    "Ellis":     "6g246PcGRvGv7HWC",
    "Marco":     "6g246PhcFf67xGwC",
    "Blocked":   "6g246Pjqp8jGCjXC",
    "Recurring": "6g246Q2vpQXq9HMj",
}


def get_token() -> str:
    """Resolve token: env → cache → 1Password CLI."""
    # 1) Env var
    tok = os.getenv("TODOIST_TOKEN", "").strip()
    if tok and len(tok) >= 10:
        return _clean_token(tok)

    # 2) Cache file
    if TOKEN_CACHE.exists():
        tok = TOKEN_CACHE.read_text().strip()
        if tok and len(tok) >= 10:
            return _clean_token(tok)

    # 3) 1Password CLI
    try:
        raw = subprocess.check_output(
            ["op", "read", ONEPASSWORD_ITEM_REF],
            text=True, timeout=30
        ).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(
            "Could not read Todoist token. Set TODOIST_TOKEN env var or run:\n"
            "  op read 'op://Private/Todoist Token/notesPlain' > ~/.todoist_token\n"
            f"Error: {e}"
        ) from e

    if not raw:
        raise RuntimeError("Todoist token is empty in 1Password item")

    tok = _clean_token(raw)

    # Cache for next time
    TOKEN_CACHE.write_text(tok + "\n")
    TOKEN_CACHE.chmod(0o600)
    print(f"[info] Token cached to {TOKEN_CACHE}")

    return tok


def _clean_token(raw: str) -> str:
    """Handle formats like 'TODOIST_API_TOKEN: abc123'."""
    token = raw.strip()
    if ":" in token:
        token = token.split(":", 1)[1].strip()
    if " " in token:
        token = token.split()[-1].strip()
    if not token or len(token) < 10:
        raise RuntimeError(f"Token looks invalid (len={len(token)})")
    return token


def api(method: str, path: str, payload=None):
    """Make a Todoist API request. Returns (status_code, parsed_json)."""
    token = get_token()
    url = f"{TODOIST_API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8")
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Todoist API {e.code}: {detail}")


def _results(data):
    """Normalize paginated response to list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "results" in data:
            return data["results"]
        return [v for v in data.values() if isinstance(v, dict)]
    return []


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_test(_args=None):
    status, data = api("GET", "/projects")
    projects = _results(data)
    print(f"✅ Auth OK (HTTP {status}). {len(projects)} projects:")
    for p in projects:
        print(f"  • {p.get('id')}: {p.get('name')}")


def cmd_setup(args):
    projects = _results(api("GET", "/projects")[1])
    project = next((p for p in projects if p.get("name") == args.project_name), None)

    if project is None:
        _, project = api("POST", "/projects", {"name": args.project_name})
        print(f"Created project: {project.get('id')} — {project.get('name')}")
    else:
        print(f"Project exists: {project.get('id')} — {project.get('name')}")

    pid = str(project.get("id"))
    existing = {s.get("name") for s in _results(api("GET", f"/sections?project_id={pid}")[1])}
    for name in ["Ellis", "Marco", "Blocked", "Recurring"]:
        if name in existing:
            print(f"  Section exists: {name}")
        else:
            _, sec = api("POST", "/sections", {"project_id": pid, "name": name})
            print(f"  Created section: {sec.get('id')} — {sec.get('name')}")


def cmd_add(args):
    payload = {"content": args.content}
    payload["project_id"] = args.project_id or DEFAULT_PROJECT_ID
    if args.section:
        sid = SECTION_MAP.get(args.section, args.section)
        payload["section_id"] = sid
    if args.due_string:
        payload["due_string"] = args.due_string
    if args.priority:
        payload["priority"] = args.priority
    status, task = api("POST", "/tasks", payload)
    print(f"✅ Created task (HTTP {status}): {task.get('id')} — {task.get('content')}")
    return task


def cmd_list(args):
    pid = args.project_id or DEFAULT_PROJECT_ID
    if args.filter:
        status, data = api("POST", "/tasks/filter", {"query": args.filter})
        tasks = _results(data)
    else:
        status, data = api("GET", f"/tasks?project_id={pid}")
        tasks = _results(data)
    print(f"📋 Tasks (HTTP {status}): {len(tasks)} found")
    for t in tasks[:30]:
        due = ""
        if isinstance(t.get("due"), dict):
            due = f" (due: {t['due'].get('date', '')})"
        sec_id = t.get("section_id", "")
        sec_name = next((k for k, v in SECTION_MAP.items() if v == sec_id), "")
        sec_tag = f" [{sec_name}]" if sec_name else ""
        print(f"  • {t.get('id')}: {t.get('content')}{sec_tag}{due}")
    return tasks


def cmd_close(args):
    status, _ = api("POST", f"/tasks/{args.task_id}/close", {})
    print(f"✅ Closed task {args.task_id} (HTTP {status})")


def cmd_sync(_args=None):
    """Sync data/task_tracker.md tables → Todoist Business Ops (idempotent)."""
    if not TASK_TRACKER.exists():
        print(f"❌ task_tracker.md not found at {TASK_TRACKER}")
        sys.exit(1)

    section = None
    local_tasks = []  # list[(content, section_name)]

    for raw in TASK_TRACKER.read_text().splitlines():
        line = raw.strip()

        if line.startswith("## 🟢 Ellis Handles"):
            section = "Ellis"
            continue
        if line.startswith("## 🟡 Marco Action"):
            section = "Marco"
            continue
        if line.startswith("## 🔴 Blocked"):
            section = "Blocked"
            continue
        if line.startswith("## ✅ Completed"):
            section = "Completed"
            continue

        # Parse markdown table rows only in active sections
        if not section or section == "Completed" or not line.startswith("|"):
            continue
        if line.startswith("|---"):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if cells[0] == "#" or cells[1].lower() == "task":
            continue

        task_text = cells[1]
        status_text = " ".join(cells[4:]).lower()
        if any(k in status_text for k in ["✅", "complete", "completed", "done"]):
            continue

        if task_text:
            local_tasks.append((task_text[:220], section))

    if not local_tasks:
        print("No open tasks in tracker.")
        return

    print(f"📄 Found {len(local_tasks)} open tasks in tracker")

    # Get existing Todoist tasks in Business Ops
    _, data = api("GET", f"/tasks?project_id={DEFAULT_PROJECT_ID}")
    existing = _results(data)
    existing_contents = {t.get("content", "").lower() for t in existing}

    created = 0
    skipped = 0
    for task_text, sec in local_tasks:
        # Idempotency: case-insensitive prefix matching
        prefix = task_text[:60].lower()
        if any(prefix in ec for ec in existing_contents):
            print(f"  ⏭ Already exists: {task_text[:90]}...")
            skipped += 1
            continue

        _, t = api("POST", "/tasks", {
            "content": task_text,
            "project_id": DEFAULT_PROJECT_ID,
            "section_id": SECTION_MAP.get(sec, SECTION_MAP["Ellis"]),
        })
        print(f"  ✅ Created [{sec}]: {t.get('id')} — {t.get('content', '')[:80]}")
        existing_contents.add((t.get("content") or "").lower())
        created += 1

    print(f"\n🔄 Sync complete: {created} created, {skipped} skipped (already existed)")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Todoist bridge — MVP")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("test", help="Verify auth")

    p_setup = sub.add_parser("setup", help="Ensure project + sections")
    p_setup.add_argument("--project-name", default="Business Ops")

    p_add = sub.add_parser("add", help="Create a task")
    p_add.add_argument("--content", required=True)
    p_add.add_argument("--project-id", default=None)
    p_add.add_argument("--section", default=None, help="Section name: Ellis/Marco/Blocked/Recurring")
    p_add.add_argument("--due-string", default=None)
    p_add.add_argument("--priority", type=int, choices=[1, 2, 3, 4], default=None)

    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("--filter", default=None)
    p_list.add_argument("--project-id", default=None)

    p_close = sub.add_parser("close", help="Complete a task")
    p_close.add_argument("--task-id", required=True)

    sub.add_parser("sync", help="Sync task_tracker.md → Todoist")

    args = parser.parse_args()
    handlers = {
        "test": cmd_test,
        "setup": cmd_setup,
        "add": cmd_add,
        "list": cmd_list,
        "close": cmd_close,
        "sync": cmd_sync,
    }
    try:
        handlers[args.cmd](args)
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
