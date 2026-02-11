#!/usr/bin/env python3
"""Check whether recent user instructions were captured into memory files."""

import json
import os
import glob
import re
from datetime import datetime

WORKSPACE = "/Users/ellisbot/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
TOPICS_DIR = os.path.join(MEMORY_DIR, "topics")
SESSIONS_DIR = "/Users/ellisbot/.openclaw/agents/main/sessions"
REPORT_DIR = os.path.join(WORKSPACE, "data", "integrity_reports")

KEY_PATTERNS = [
    r"from now on", r"always", r"never", r"make sure", r"i want",
    r"kill", r"pause", r"approved", r"cut", r"change", r"priority",
    r"\$\d", r"\d+%", r"deadline", r"due", r"remember",
]


def load_recent_user_messages(limit=80):
    msgs = []
    files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.jsonl")), key=os.path.getmtime, reverse=True)[:3]
    for sf in files:
        try:
            with open(sf, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    msg = obj.get("message", {})
                    if msg.get("role") != "user":
                        continue
                    text = "\n".join(c.get("text", "") for c in msg.get("content", []) if isinstance(c, dict) and c.get("type") == "text")
                    if text.strip():
                        msgs.append(text.strip())
        except Exception:
            continue
    return msgs[-limit:]


def interesting_lines(messages):
    out = []
    rx = re.compile("|".join(KEY_PATTERNS), re.I)
    for m in messages:
        for line in m.split("\n"):
            line = line.strip()
            if line and rx.search(line):
                out.append(line)
    return out


def memory_blob():
    parts = []
    for path in [os.path.join(WORKSPACE, "MEMORY.md")]:
        if os.path.exists(path):
            parts.append(open(path, "r").read().lower())
    for tf in ["business.md", "preferences.md", "systems.md", "agents.md", "lessons.md"]:
        p = os.path.join(TOPICS_DIR, tf)
        if os.path.exists(p):
            parts.append(open(p, "r").read().lower())
    today = datetime.now().strftime("%Y-%m-%d")
    dp = os.path.join(MEMORY_DIR, f"{today}.md")
    if os.path.exists(dp):
        parts.append(open(dp, "r").read().lower())
    return "\n".join(parts)


def line_signature(line):
    line = re.sub(r"[^a-zA-Z0-9\s$%]", "", line.lower())
    words = [w for w in line.split() if len(w) > 3]
    return words[:6]


def main():
    msgs = load_recent_user_messages()
    lines = interesting_lines(msgs)
    blob = memory_blob()

    missing = []
    for ln in lines:
        sig = line_signature(ln)
        if not sig:
            continue
        if not any(w in blob for w in sig[:3]):
            missing.append(ln)

    os.makedirs(REPORT_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = os.path.join(REPORT_DIR, f"memory_integrity_{now}.json")
    report = {
        "timestamp": datetime.now().isoformat(),
        "checked_lines": len(lines),
        "missing_count": len(missing),
        "missing_examples": missing[:10],
        "status": "ok" if len(missing) == 0 else "gaps",
    }
    with open(out, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
