#!/usr/bin/env python3
"""
Task Integrity Check — Automated Safety Net
=============================================

PURPOSE:
  Ellis keeps saying "Done" when Marco asks to update tasks, but doesn't
  actually update task_tracker.md or the pinned message in #tasks. This
  script catches those gaps automatically.

HOW IT WORKS:
  This is NOT a standalone runnable script. It's a REFERENCE IMPLEMENTATION
  that the main agent (Ellis) executes step-by-step during heartbeat checks
  using the OpenClaw message tool and file system.

  The heartbeat workflow:
    1. Read recent messages from all known channels (last 2 hours)
    2. Scan for task-related phrases (add, remove, remind patterns)
    3. Read current task_tracker.md
    4. Compare: any mentioned tasks not reflected in tracker?
    5. Output JSON report of gaps
    6. If gaps found → alert in #system channel

INTEGRATION:
  Add to HEARTBEAT.md:
    - [ ] Run task integrity check (every 2 hours)

CHANNELS TO SCAN:
  All active channels — #general, #braindump, #tasks, #growth, #finance,
  #analytics, #system, and any DMs with Marco.

Author: Ellis (subagent)
Created: 2026-02-11
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

# ─── Configuration ───────────────────────────────────────────────────────────

TASK_TRACKER_PATH = "/Users/ellisbot/.openclaw/workspace/data/task_tracker.md"

# Patterns that indicate a task is being ADDED or REQUESTED
ADD_PATTERNS = [
    r"add\s+(this\s+)?to\s+(the\s+)?task",
    r"put\s+(this\s+)?on\s+(the\s+)?task",
    r"on\s+the\s+task\s+list",
    r"add\s+this\s+to",
    r"put\s+this\s+on",
    r"make\s+sure\s+(you\s+)?to",
    r"don'?t\s+forget\s+to",
    r"remind\s+me\s+to",
    r"need\s+to\s+add",
    r"add\s+it\s+to\s+(the\s+)?(list|tracker|board)",
    r"put\s+it\s+on\s+(the\s+)?(list|tracker|board)",
    r"track\s+this",
    r"add\s+a\s+task",
]

# Patterns that indicate a task is DONE or should be REMOVED
DONE_PATTERNS = [
    r"is\s+done",
    r"is\s+complete[d]?",
    r"finished\s+(with\s+)?",
    r"remove\s+from\s+(the\s+)?task",
    r"take\s+(this\s+)?off\s+(the\s+)?(list|tracker|board)",
    r"take\s+that\s+off",
    r"mark\s+(it\s+|that\s+)?as\s+(done|complete)",
    r"cross\s+(it|that)\s+off",
    r"done\s+with\s+",
    r"got\s+(the\s+)?\w+\s+done",
    r"already\s+did",
    r"that'?s\s+done",
    r"checked\s+off",
]

# Compile all patterns
ADD_RE = [re.compile(p, re.IGNORECASE) for p in ADD_PATTERNS]
DONE_RE = [re.compile(p, re.IGNORECASE) for p in DONE_PATTERNS]


def scan_message(text: str) -> Optional[dict]:
    """Check if a message contains task-related phrases.
    
    Returns dict with match info or None.
    """
    for pattern in ADD_RE:
        match = pattern.search(text)
        if match:
            return {
                "type": "add",
                "pattern": pattern.pattern,
                "matched_text": match.group(),
                "full_message": text.strip(),
            }
    
    for pattern in DONE_RE:
        match = pattern.search(text)
        if match:
            return {
                "type": "done",
                "pattern": pattern.pattern,
                "matched_text": match.group(),
                "full_message": text.strip(),
            }
    
    return None


def load_tracker(path: str = TASK_TRACKER_PATH) -> str:
    """Load task tracker contents."""
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return ""


def check_task_in_tracker(message_text: str, tracker_content: str) -> bool:
    """Fuzzy check if a task mentioned in a message appears in the tracker.
    
    Extracts key nouns/phrases from the message and checks if any
    appear in the tracker content. This is intentionally loose —
    better to have false negatives (miss a match) than false positives
    (miss a gap).
    """
    # Extract words longer than 4 chars as potential task identifiers
    words = re.findall(r'\b[a-zA-Z]{5,}\b', message_text.lower())
    # Remove common filler words
    filler = {
        'about', 'after', 'again', 'before', 'being', 'below', 'between',
        'could', 'doing', 'during', 'every', 'first', 'found', 'going',
        'gonna', 'gotta', 'great', 'having', 'heard', 'house', 'isn\'t',
        'known', 'later', 'least', 'maybe', 'might', 'never', 'other',
        'their', 'there', 'these', 'thing', 'think', 'those', 'today',
        'under', 'until', 'wants', 'where', 'which', 'while', 'would',
        'write', 'tasks', 'tracker', 'board', 'remember', 'forget',
        'should', 'please', 'still', 'right', 'really', 'actually',
        'already', 'pretty', 'stuff', 'things', 'needs',
    }
    keywords = [w for w in words if w not in filler]
    
    if not keywords:
        return False  # Can't determine — flag it
    
    tracker_lower = tracker_content.lower()
    # If 2+ keywords match, consider it tracked
    matches = sum(1 for kw in keywords if kw in tracker_lower)
    return matches >= 2 or (len(keywords) == 1 and keywords[0] in tracker_lower)


def generate_report(messages: List[dict], tracker_content: str) -> dict:
    """Generate integrity report.
    
    Args:
        messages: List of dicts with keys: channel, author, content, timestamp
        tracker_content: Current task_tracker.md contents
    
    Returns:
        JSON-serializable report dict
    """
    findings = []
    
    for msg in messages:
        # Skip bot messages (Ellis's own messages)
        if msg.get("is_bot", False):
            continue
        
        result = scan_message(msg["content"])
        if result is None:
            continue
        
        in_tracker = check_task_in_tracker(msg["content"], tracker_content)
        
        finding = {
            "channel": msg.get("channel", "unknown"),
            "author": msg.get("author", "unknown"),
            "timestamp": msg.get("timestamp", "unknown"),
            "message": result["full_message"],
            "action_type": result["type"],  # "add" or "done"
            "matched_pattern": result["matched_text"],
            "found_in_tracker": in_tracker,
            "gap": not in_tracker,
        }
        findings.append(finding)
    
    gaps = [f for f in findings if f["gap"]]
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "messages_scanned": len(messages),
        "task_mentions_found": len(findings),
        "gaps_detected": len(gaps),
        "status": "GAPS_FOUND" if gaps else "ALL_CLEAR",
        "findings": findings,
        "gaps": gaps,
    }
    
    return report


# ─── Heartbeat Integration Instructions ─────────────────────────────────────
#
# During heartbeat, the agent should:
#
# 1. For each channel, use the message tool to read recent messages:
#      message(action="read", channel="<channel_id>", limit=50)
#
# 2. Filter to messages from the last 2 hours
#
# 3. Collect into a list of dicts:
#      [{"channel": "#general", "author": "Marco", "content": "...", 
#        "timestamp": "...", "is_bot": False}, ...]
#
# 4. Load tracker:
#      tracker = load_tracker()
#
# 5. Generate report:
#      report = generate_report(messages, tracker)
#
# 6. If report["status"] == "GAPS_FOUND":
#      - Post alert to #system
#      - Include gap details
#      - IMMEDIATELY fix the gaps (update tracker, repin)
#
# 7. Save report to /workspace/data/integrity_reports/YYYY-MM-DD_HH.json
#
# ─────────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    # Self-test with example messages
    test_messages = [
        {"channel": "#general", "author": "Marco", "content": "Add the PO Box thing to the task list", "timestamp": "2026-02-11T07:00:00", "is_bot": False},
        {"channel": "#braindump", "author": "Marco", "content": "Don't forget to check on the CPC certs", "timestamp": "2026-02-11T07:30:00", "is_bot": False},
        {"channel": "#general", "author": "Marco", "content": "The liquidation move is done", "timestamp": "2026-02-11T07:45:00", "is_bot": False},
        {"channel": "#general", "author": "Ellis", "content": "Done! I've updated the tracker.", "timestamp": "2026-02-11T07:01:00", "is_bot": True},
        {"channel": "#general", "author": "Marco", "content": "Hey what's up", "timestamp": "2026-02-11T06:00:00", "is_bot": False},
    ]
    
    tracker = load_tracker()
    report = generate_report(test_messages, tracker)
    print(json.dumps(report, indent=2))
