# Memory System - Best Practices

## Overview

The OpenClaw memory system has two layers:

1. **MEMORY.md** (long-term, curated) — Your permanent memory
2. **memory/YYYY-MM-DD.md** (daily, raw) — Day-by-day logs

Think of it like a human brain:
- Daily files = short-term memory (what happened today)
- MEMORY.md = long-term memory (what you want to remember forever)

---

## How to Use Memory

### Daily Memory Files (`memory/YYYY-MM-DD.md`)

**Write to daily files when:**
- Recording what happened in a session
- Logging decisions made today
- Tracking issues/bugs encountered
- Noting things to remember for tomorrow

**Format:**
```markdown
# YYYY-MM-DD

## HH:MM - Event/Task Title

Description of what happened, what was decided, or what needs follow-up.

Key details, links, file paths, etc.
```

**Examples:**
```markdown
# 2026-02-02

## 13:27 - Sellerboard Velocity Integration Complete

All 3 brands now have real 90-day sales data:
- Black Owned: 56 SKUs, 15,175 units, $361,125 revenue
- Card Plug: 72 SKUs, 14,151 units, $269,187 revenue
- Kinfolk: 46 SKUs, 13,421 units, $267,472 revenue

Data source: "Dashboard by product" CSV exports
Output: /workspace/data/sku_velocity.json

## 11:54 - Switched Default Model to Claude Sonnet 4.5

Changed from OpenAI Codex to Claude Sonnet 4.5 as primary model.
OpenAI Codex remains available but not default.
All cron jobs updated to use Claude.
```

---

### Long-Term Memory (`MEMORY.md`)

**Update MEMORY.md when:**
- You learn something that will matter next week/month
- A major decision is made (tool choices, workflow changes)
- New access/credentials are granted
- Business rules/policies are established
- Repeating patterns emerge that should be codified

**What NOT to put in MEMORY.md:**
- Temporary status updates
- Things that will be stale in a few days
- Secrets/passwords (use 1Password or secure storage)
- Detailed logs (keep those in daily files)

**Structure:**
```markdown
# MEMORY.md - Long-Term Memory

*Last updated: YYYY-MM-DD*

## The Business
(Marco's business model, brands, goals)

## Working With Marco
(Preferences, communication style, boundaries)

## Access
(Systems available, authentication methods)

## Current Priority
(Active projects/focus areas)

## Lessons & Notes
(Key learnings, decisions, patterns)
```

---

## Memory Maintenance

### Weekly Review (Automated)

Every Sunday at 8 PM CST, a cron job runs to:
1. Read the last 7 days of daily memory files
2. Identify significant events/decisions/lessons
3. Suggest updates to MEMORY.md

**You should manually review and apply suggestions** — don't auto-append everything.

### Manual Consolidation

When daily files pile up, run:
```bash
python3 scripts/memory_manager.py --consolidate --days 7
```

This will suggest content to move from daily files → MEMORY.md.

### Memory Health Check

Check system status anytime:
```bash
python3 scripts/memory_manager.py --report
```

### Search Old Memories

Find past context:
```bash
python3 scripts/memory_manager.py --search "keyword"
```

### Cleanup Old Files

Archive files older than 90 days:
```bash
python3 scripts/memory_manager.py --cleanup --older-than 90
```

---

## Memory Search (Semantic)

OpenClaw includes **semantic memory search** powered by local embeddings.

**When to use `memory_search`:**
- User asks about prior work/decisions
- Need to recall dates, people, preferences
- Looking for past context on a project
- Checking if something was already discussed

**Example:**
```python
memory_search("sellerboard velocity integration")
```

Returns relevant snippets from MEMORY.md and daily files.

**Note:** The index syncs automatically when files change. If results seem stale, the system may still be indexing.

---

## Tips for Good Memory Hygiene

1. **Write daily files in real-time** — Don't wait until end of session
2. **Be specific** — Include file paths, commands, exact decisions
3. **Update MEMORY.md weekly** — Review recent dailies and promote what matters
4. **Archive old dailies** — Move files older than 90 days to `memory/archive/`
5. **Don't duplicate** — If it's in MEMORY.md, don't repeat in every daily file
6. **No secrets** — Use 1Password for credentials, never plain text in memory files

---

## When the Agent Wakes Up

Every session, the agent should:
1. Read **SOUL.md** (who you are)
2. Read **USER.md** (who you're helping)
3. Read **MEMORY.md** (what you know)
4. Read **today's daily file** + **yesterday's daily file** (recent context)

This ensures continuity across sessions.

---

## Troubleshooting

**Problem:** Daily files aren't being created  
**Fix:** Make sure cron jobs are running and writing to daily files

**Problem:** MEMORY.md is getting too long (>10KB)  
**Fix:** Archive less-relevant sections, keep only what's actively useful

**Problem:** memory_search returns no results  
**Fix:** Wait for indexing to complete; check that files actually contain the search terms

**Problem:** Old memories are cluttering the workspace  
**Fix:** Run `memory_manager.py --cleanup` and move old files to archive

---

## Philosophy

> "Memory is not about storing everything — it's about remembering what matters."

The goal is **curated continuity**, not exhaustive logs. Write enough to remember context, but not so much that future-you drowns in noise.

Be ruthless about what you promote to MEMORY.md. If you wouldn't want to read it in 3 months, it doesn't belong there.

---

*This document is itself part of the memory system. Update it as workflows improve.*
