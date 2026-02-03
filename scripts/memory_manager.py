#!/usr/bin/env python3
"""
Memory Management Script for OpenClaw Workspace

Provides tools for:
- Consolidating daily memory files into MEMORY.md
- Cleaning up old/stale entries
- Generating memory reports
- Finding relevant past context

Usage:
    python3 memory_manager.py --consolidate [--days 7]
    python3 memory_manager.py --report
    python3 memory_manager.py --search "keyword"
    python3 memory_manager.py --cleanup [--older-than 90]
"""

import argparse
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_MD = WORKSPACE / "MEMORY.md"


def get_recent_memory_files(days=7):
    """Get memory files from the last N days."""
    files = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for f in MEMORY_DIR.glob("????-??-??.md"):
        try:
            date_str = f.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date >= cutoff:
                files.append((file_date, f))
        except ValueError:
            continue
    
    return sorted(files, key=lambda x: x[0])


def read_memory_md():
    """Read current MEMORY.md content."""
    if MEMORY_MD.exists():
        return MEMORY_MD.read_text()
    return ""


def extract_sections(content):
    """Extract sections from MEMORY.md by heading."""
    sections = defaultdict(list)
    current_section = "header"
    
    for line in content.split("\n"):
        if line.startswith("## "):
            current_section = line[3:].strip()
        else:
            sections[current_section].append(line)
    
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def consolidate_memories(days=7):
    """Consolidate recent daily memories into MEMORY.md."""
    recent_files = get_recent_memory_files(days)
    
    if not recent_files:
        print(f"⚠️  No memory files found in last {days} days")
        return
    
    print(f"📚 Reading {len(recent_files)} memory files from last {days} days...")
    
    # Collect key events/decisions
    events = []
    decisions = []
    lessons = []
    
    for date, filepath in recent_files:
        content = filepath.read_text()
        date_str = date.strftime("%b %d, %Y")
        
        # Look for patterns indicating important content
        if re.search(r'(decision|decided|chose|switching|changed)', content, re.I):
            decisions.append(f"- **{date_str}:** {content[:200]}...")
        
        if re.search(r'(lesson|learned|mistake|fixed|issue)', content, re.I):
            lessons.append(f"- **{date_str}:** {content[:200]}...")
        
        if re.search(r'(completed|shipped|launched|deployed)', content, re.I):
            events.append(f"- **{date_str}:** {content[:200]}...")
    
    print(f"✓ Found {len(decisions)} decisions, {len(lessons)} lessons, {len(events)} events")
    
    # Read current MEMORY.md
    current = read_memory_md()
    sections = extract_sections(current)
    
    # Update timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n📝 Suggestions for MEMORY.md updates:")
    print(f"   (Review and manually apply what's relevant)\n")
    
    if decisions:
        print("## Recent Decisions:")
        for d in decisions[:5]:  # Top 5
            print(d)
        print()
    
    if lessons:
        print("## Recent Lessons:")
        for l in lessons[:5]:
            print(l)
        print()
    
    if events:
        print("## Recent Events:")
        for e in events[:5]:
            print(e)
        print()
    
    print(f"ℹ️  Manual review recommended — don't auto-append everything!")


def generate_report():
    """Generate a memory system health report."""
    print("🧠 MEMORY SYSTEM REPORT")
    print("=" * 60)
    
    # Check MEMORY.md
    if MEMORY_MD.exists():
        size = MEMORY_MD.stat().st_size
        lines = len(MEMORY_MD.read_text().split("\n"))
        print(f"\n✓ MEMORY.md exists ({size:,} bytes, {lines} lines)")
        
        # Check last update
        mtime = datetime.fromtimestamp(MEMORY_MD.stat().st_mtime)
        days_old = (datetime.now() - mtime).days
        print(f"  Last modified: {mtime.strftime('%Y-%m-%d %H:%M')} ({days_old} days ago)")
        
        if days_old > 14:
            print(f"  ⚠️  MEMORY.md hasn't been updated in {days_old} days")
    else:
        print("\n❌ MEMORY.md missing!")
    
    # Check daily memory files
    all_files = sorted(MEMORY_DIR.glob("????-??-??.md"))
    if all_files:
        print(f"\n✓ {len(all_files)} daily memory files found")
        oldest = all_files[0].stem
        newest = all_files[-1].stem
        print(f"  Range: {oldest} → {newest}")
        
        # Check if today's file exists
        today = datetime.now().strftime("%Y-%m-%d")
        today_file = MEMORY_DIR / f"{today}.md"
        if today_file.exists():
            print(f"  ✓ Today's memory file exists ({today_file.name})")
        else:
            print(f"  ⚠️  Today's memory file missing ({today}.md)")
    else:
        print("\n❌ No daily memory files found!")
    
    # Check memory_search status
    print("\n📊 Memory Search:")
    try:
        # Try to read config to see if memory search is enabled
        config_path = Path.home() / ".openclaw" / "openclaw.json"
        if config_path.exists():
            config = json.loads(config_path.read_text())
            mem_search = config.get("agents", {}).get("defaults", {}).get("memorySearch", {})
            enabled = mem_search.get("enabled", False)
            provider = mem_search.get("provider", "unknown")
            
            if enabled:
                print(f"  ✓ Enabled (provider: {provider})")
            else:
                print(f"  ⚠️  Disabled")
        else:
            print("  ? Config not found")
    except Exception as e:
        print(f"  ⚠️  Could not check status: {e}")
    
    # Storage stats
    print("\n💾 Storage:")
    total_size = sum(f.stat().st_size for f in MEMORY_DIR.glob("*.md"))
    print(f"  Total memory files: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    
    print("\n" + "=" * 60)


def search_memories(query, days=None):
    """Search memory files for a keyword/phrase."""
    query_lower = query.lower()
    results = []
    
    files = MEMORY_DIR.glob("????-??-??.md")
    
    for filepath in sorted(files, reverse=True):
        content = filepath.read_text()
        if query_lower in content.lower():
            date = filepath.stem
            # Get context around match
            lines = content.split("\n")
            matching_lines = [i for i, line in enumerate(lines) if query_lower in line.lower()]
            
            for line_num in matching_lines:
                start = max(0, line_num - 2)
                end = min(len(lines), line_num + 3)
                context = "\n".join(lines[start:end])
                results.append((date, context))
    
    if results:
        print(f"🔍 Found {len(results)} matches for '{query}':\n")
        for date, context in results[:10]:  # Show top 10
            print(f"📅 {date}")
            print(context)
            print("-" * 60)
    else:
        print(f"❌ No matches found for '{query}'")


def cleanup_old_files(older_than_days=90):
    """Archive or remove very old daily memory files."""
    cutoff = datetime.now() - timedelta(days=older_than_days)
    old_files = []
    
    for f in MEMORY_DIR.glob("????-??-??.md"):
        try:
            date_str = f.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                old_files.append(f)
        except ValueError:
            continue
    
    if not old_files:
        print(f"✓ No files older than {older_than_days} days")
        return
    
    print(f"⚠️  Found {len(old_files)} files older than {older_than_days} days:")
    for f in old_files:
        print(f"  - {f.name}")
    
    print(f"\n💡 Suggestion: Review and consolidate important content into MEMORY.md,")
    print(f"   then move old files to memory/archive/ to keep workspace clean.")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Memory Manager")
    parser.add_argument("--consolidate", action="store_true", 
                       help="Consolidate recent daily memories")
    parser.add_argument("--report", action="store_true", 
                       help="Generate memory system health report")
    parser.add_argument("--search", type=str, 
                       help="Search memory files for keyword")
    parser.add_argument("--cleanup", action="store_true", 
                       help="Identify old files for cleanup")
    parser.add_argument("--days", type=int, default=7, 
                       help="Number of days to look back (default: 7)")
    parser.add_argument("--older-than", type=int, default=90, 
                       help="Cleanup threshold in days (default: 90)")
    
    args = parser.parse_args()
    
    if args.consolidate:
        consolidate_memories(days=args.days)
    elif args.report:
        generate_report()
    elif args.search:
        search_memories(args.search, days=args.days)
    elif args.cleanup:
        cleanup_old_files(older_than_days=args.older_than)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
