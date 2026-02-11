#!/usr/bin/env python3
"""Memory Autocapture — Extract decisions from conversation transcripts and file them."""

import argparse
import os
import re
import sys
from datetime import datetime

WORKSPACE = "/Users/ellisbot/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
TOPICS_DIR = os.path.join(MEMORY_DIR, "topics")

# Known brands/people/projects for tagging
KNOWN_TAGS = [
    "kinfolk", "card plug", "black love", "black owned", "marco", "ellis",
    "codex", "opus", "vibe", "atlas", "sellerboard", "amazon", "ads",
    "shopify", "tiktok", "instagram", "facebook", "google",
]

# Pattern definitions: (compiled_regex, type, title_extractor)
PATTERNS = [
    # RULE / PREFERENCE patterns
    (re.compile(r'(?:from now on|always|never|make sure|I want|I need you to)\s+(.+)', re.I), "RULE", None),
    (re.compile(r'(?:I prefer|I like it when|do it like|the way I want)\s+(.+)', re.I), "PREFERENCE", None),
    # DECISION patterns
    (re.compile(r'(?:let\'?s go with|kill|pause|approved|cut|change to|remove|removing|switch to|cancel)\s+(.+)', re.I), "DECISION", None),
    (re.compile(r'(?:we\'?re going with|decided on|picking|chose|going to use)\s+(.+)', re.I), "DECISION", None),
    # FACT patterns (money/percentages)
    (re.compile(r'(.+?\$[\d,]+[kKmM]?\b.+)', re.I), "FACT", None),
    (re.compile(r'(.+?\d+\.?\d*\s*%.+)', re.I), "FACT", None),
    (re.compile(r'(?:remember|don\'?t forget|note that|FYI|for the record)\s+(.+)', re.I), "FACT", None),
    # COMMITMENT patterns
    (re.compile(r'(?:by |deadline|I\'?ll have|need this done|due |deliver by)\s*(.+)', re.I), "COMMITMENT", None),
    (re.compile(r'(.+?)\s+(?:by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|end of|next))', re.I), "COMMITMENT", None),
    # DIRECTION patterns
    (re.compile(r'(?:focus on|priority|moving forward|strategy|this quarter|going forward|pivot to)\s*(.+)', re.I), "DIRECTION", None),
    (re.compile(r'(?:let\'?s focus on)\s+(.+)', re.I), "DIRECTION", None),
]

# Filing map: type -> topic file
FILING_MAP = {
    "PREFERENCE": "preferences.md",
    "RULE": "preferences.md",
    "DECISION": "business.md",
    "FACT": "business.md",  # default; overridden for systems/agents
    "COMMITMENT": "business.md",
    "DIRECTION": "business.md",
}

SYSTEM_KEYWORDS = ["tool", "system", "access", "api", "login", "password", "server", "deploy", "ssh", "database", "integration"]
AGENT_KEYWORDS = ["agent", "codex", "opus", "vibe", "atlas", "protocol", "validation", "cross-check"]
LESSON_KEYWORDS = ["lesson", "mistake", "learned", "never again", "bug", "fix", "broke", "wrong", "error"]


def extract_tags(text):
    """Extract known tags from text."""
    text_lower = text.lower()
    tags = []
    for tag in KNOWN_TAGS:
        if tag in text_lower:
            tags.append(tag)
    return tags if tags else ["general"]


def determine_file(item_type, content, tags):
    """Determine which topic file to write to."""
    content_lower = content.lower()
    if any(kw in content_lower for kw in LESSON_KEYWORDS):
        return "lessons.md"
    if item_type == "FACT":
        if any(kw in content_lower for kw in SYSTEM_KEYWORDS):
            return "systems.md"
        if any(kw in content_lower for kw in AGENT_KEYWORDS):
            return "agents.md"
    return FILING_MAP.get(item_type, "business.md")


def extract_items(text):
    """Extract memory items from conversation text."""
    today = datetime.now().strftime("%Y-%m-%d")
    items = []
    seen_content = set()
    human_speakers = {"marco", "lewisg", "user", "owner"}

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        speaker = "unknown"
        utterance = line

        # Expected format: "Speaker: message"
        speaker_match = re.match(r'^([^:]{1,40}):\s*(.+)', line)
        if speaker_match:
            speaker, utterance = speaker_match.group(1).strip(), speaker_match.group(2).strip()

        # Ignore assistant/bot lines; process likely-human lines only
        s = speaker.lower()
        if s and s not in human_speakers:
            # If unknown speaker but line contains direct instruction language, keep it
            if not re.search(r'\b(from now on|always|never|i want|make sure|let\'s|approved|kill|priority|remember)\b', utterance, re.I):
                continue

        for pattern, item_type, _ in PATTERNS:
            m = pattern.search(utterance)
            if m:
                content = utterance.strip()
                if content in seen_content:
                    break
                seen_content.add(content)

                tags = extract_tags(content)
                target_file = determine_file(item_type, content, tags)

                title_words = content.split()[:6]
                title = " ".join(title_words)
                if len(content.split()) > 6:
                    title += "..."

                supersedes = None
                if re.search(r'\b(actually|instead|change to|switch to|no longer|replace)\b', content, re.I):
                    supersedes = "prior decision on same topic"

                items.append({
                    "type": item_type,
                    "title": title,
                    "content": content,
                    "date": today,
                    "tags": tags,
                    "target_file": target_file,
                    "supersedes": supersedes,
                })
                break

    return items


def format_entry(item):
    """Format a memory item for a topic file."""
    lines = [
        f"### {item['type']} {item['title']} ({item['date']})",
        item['content'],
        f"Tags: {', '.join(item['tags'])}",
    ]
    if item.get('supersedes'):
        lines.append(f"Supersedes: {item['supersedes']}")
    lines.append("")
    return "\n".join(lines)


def format_daily(item):
    """Format a one-liner for the daily log."""
    return f"- **[{item['type']}]** {item['content']}"


def content_exists(filepath, content, check_lines=10):
    """Check if similar content already exists in the file (last N lines)."""
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
        tail = "".join(lines[-check_lines:]) if len(lines) >= check_lines else "".join(lines)
        # Check if the core content is already there
        return content.strip() in tail
    except Exception:
        return False


def ensure_file(filepath, header=""):
    """Ensure a file exists, creating with header if needed."""
    if not os.path.exists(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(header + "\n")


def append_to_file(filepath, text):
    """Append text to a file."""
    with open(filepath, "a") as f:
        f.write("\n" + text)


def main():
    parser = argparse.ArgumentParser(description="Extract memory items from conversation transcripts")
    parser.add_argument("--file", help="Path to transcript file (otherwise reads stdin)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--daily-only", action="store_true", help="Only write to daily log")
    args = parser.parse_args()

    # Read input
    if args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("No input provided.")
        sys.exit(1)

    items = extract_items(text)
    if not items:
        print("No actionable items extracted.")
        sys.exit(0)

    today = datetime.now().strftime("%Y-%m-%d")
    daily_path = os.path.join(MEMORY_DIR, f"{today}.md")
    daily_header = f"# Daily Log — {today}\n\n## Auto-Captured\n"

    print(f"\n📝 Extracted {len(items)} item(s):\n")

    for item in items:
        entry = format_entry(item)
        daily_line = format_daily(item)
        topic_path = os.path.join(TOPICS_DIR, item["target_file"])

        print(f"  [{item['type']}] {item['content']}")
        print(f"    → {item['target_file']}  |  Tags: {', '.join(item['tags'])}")

        if args.dry_run:
            print(f"    (dry-run) Would append to: {topic_path}")
            print(f"    (dry-run) Would log to: {daily_path}")
            print()
            continue

        # Write to daily log
        if not content_exists(daily_path, item["content"]):
            ensure_file(daily_path, daily_header)
            append_to_file(daily_path, daily_line)
            print(f"    ✅ Logged to daily")
        else:
            print(f"    ⏭️  Already in daily log")

        # Write to topic file (unless --daily-only)
        if not args.daily_only:
            if not content_exists(topic_path, item["content"]):
                ensure_file(topic_path, f"# {item['target_file'].replace('.md', '').title()}\n")
                append_to_file(topic_path, entry)
                print(f"    ✅ Filed to {item['target_file']}")
            else:
                print(f"    ⏭️  Already in {item['target_file']}")

        print()

    print(f"Done. {len(items)} items processed.")


if __name__ == "__main__":
    main()
