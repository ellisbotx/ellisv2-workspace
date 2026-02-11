#!/usr/bin/env python3
"""Ingest new user messages from OpenClaw session JSONL logs into memory topic files."""

import json
import os
import glob
from datetime import datetime, timezone

from memory_autocapture import extract_items, format_entry, format_daily, content_exists, ensure_file, append_to_file

WORKSPACE = "/Users/ellisbot/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
TOPICS_DIR = os.path.join(MEMORY_DIR, "topics")
SESSIONS_DIR = "/Users/ellisbot/.openclaw/agents/main/sessions"
CHECKPOINT = os.path.join(MEMORY_DIR, ".ingest_checkpoint.json")


def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        try:
            with open(CHECKPOINT, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_checkpoint(data):
    with open(CHECKPOINT, "w") as f:
        json.dump(data, f, indent=2)


def parse_ts(ts):
    if not ts:
        return 0.0
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def extract_user_texts(session_file, last_ts):
    rows = []
    newest = last_ts
    with open(session_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            msg = obj.get("message", {})
            role = msg.get("role")
            ts = parse_ts(obj.get("timestamp"))
            if ts <= last_ts:
                continue
            newest = max(newest, ts)

            if role != "user":
                continue

            content = msg.get("content", [])
            text_parts = []
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    text_parts.append(c.get("text", ""))
            text = "\n".join(t for t in text_parts if t).strip()
            if text:
                rows.append(text)

    return rows, newest


def normalize_to_marco_lines(text):
    lines = []
    for raw in text.split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        # Prefer explicit owner marker in bridged messages
        if "[from: LewisG" in raw or "LewisG" in raw:
            # try split on "):" pattern
            if "):" in raw:
                raw = raw.split("):", 1)[1].strip()
            lines.append(f"Marco: {raw}")
            continue
        # default user line
        lines.append(f"Marco: {raw}")
    return "\n".join(lines)


def ingest_items(items):
    today = datetime.now().strftime("%Y-%m-%d")
    daily_path = os.path.join(MEMORY_DIR, f"{today}.md")
    daily_header = f"# Daily Log — {today}\n\n## Auto-Captured\n"

    written = 0
    for item in items:
        topic_path = os.path.join(TOPICS_DIR, item["target_file"])

        if not content_exists(daily_path, item["content"], check_lines=200):
            ensure_file(daily_path, daily_header)
            append_to_file(daily_path, format_daily(item))
            written += 1

        if not content_exists(topic_path, item["content"], check_lines=200):
            ensure_file(topic_path, f"# {item['target_file'].replace('.md', '').title()}\n")
            append_to_file(topic_path, format_entry(item))
            written += 1

    return written


def main():
    checkpoint = load_checkpoint()
    session_files = sorted(glob.glob(os.path.join(SESSIONS_DIR, "*.jsonl")), key=os.path.getmtime, reverse=True)[:10]

    total_msgs = 0
    total_items = 0
    total_written = 0

    for sf in session_files:
        key = os.path.basename(sf)
        last_ts = checkpoint.get(key, 0.0)
        texts, newest = extract_user_texts(sf, last_ts)
        checkpoint[key] = newest

        for t in texts:
            total_msgs += 1
            transcript = normalize_to_marco_lines(t)
            items = extract_items(transcript)
            if items:
                total_items += len(items)
                total_written += ingest_items(items)

    # prune old checkpoints not in top files
    active = {os.path.basename(p) for p in session_files}
    checkpoint = {k: v for k, v in checkpoint.items() if k in active}
    save_checkpoint(checkpoint)

    print(f"Ingestion complete: {total_msgs} new user messages, {total_items} extracted items, {total_written} writes")


if __name__ == "__main__":
    main()
