#!/usr/bin/env python3
import json
import pathlib
import urllib.request

BASE = "https://api.todoist.com/api/v1"
PROJECT_ID = "6g246PHRgJxCFwgC"
STATE_PATH = pathlib.Path("/Users/ellisbot/.openclaw/workspace/data/todoist_sync_state.json")


def get_token():
    p = pathlib.Path.home() / ".todoist_token"
    return p.read_text().strip()


def api_get(path):
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads((r.read().decode() or "{}"))
    if isinstance(data, dict) and "results" in data:
        data = data["results"]
    return data


def load_state():
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def main():
    tasks = api_get(f"/tasks?project_id={PROJECT_ID}")
    current = {t.get("id"): t.get("content", "") for t in tasks if t.get("id")}

    prev = load_state().get("open_tasks", {})

    prev_ids = set(prev.keys())
    cur_ids = set(current.keys())

    added = [current[i] for i in sorted(cur_ids - prev_ids)]
    completed = [prev[i] for i in sorted(prev_ids - cur_ids)]

    save_state({"open_tasks": current})

    # Emit json for caller/cron agent to post
    print(json.dumps({
        "added": added,
        "completed": completed,
        "openCount": len(current),
    }))


if __name__ == "__main__":
    main()
