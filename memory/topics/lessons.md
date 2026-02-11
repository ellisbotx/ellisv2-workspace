# Lessons & Notes
*Last updated: 2026-02-10*

---

## Script vs LLM Automation (Feb 1, 2026)

- Marco prefers deterministic scripts over LLM-driven loops
- Scripts don't hallucinate, don't skip items, don't add "Mixed" confusion
- Use LLM for interpretation/reporting, not for iteration logic
- Example: ASIN checker v1 (LLM) checked 7/186 and hallucinated 3. v2 (Python) checked all 166 correctly.

## Memory System (Feb 2, 2026)

- MEMORY.md = long-term curated memory (what matters forever)
- memory/YYYY-MM-DD.md = daily logs (what happened today)
- Semantic search enabled (local embeddings via nomic-ai/nomic-embed-text-v1.5)
- Weekly consolidation cron (Sun 8 PM) reviews last 7 days, suggests MEMORY.md updates
- Memory manager script: `/workspace/scripts/memory_manager.py` (report, search, consolidate, cleanup)
- Best practices: `/workspace/memory/README.md`
- **Memory updates post to #system channel** for transparency into my learning

## Don't Say "That's On Me" — Just Don't Let It Happen (Feb 10, 2026)

Marco's standard: If you said you could do it and didn't, that's inexcusable. Don't frame failures as "learning moments." A failure is a failure. The only acceptable response is: fix it, prove it's fixed, and make sure it can't happen again. Period.

## Memory Search Was Never Working (Feb 10, 2026)

**Root cause:** TWO problems stacked on each other:
1. The qmd search index was never built — zero files indexed, zero vectors. Collections existed but `qmd update` and `qmd embed` were never run after setup.
2. Memory search scope was set to `default: "deny"` with allow only for `chatType: "direct"` — Discord guild messages were blocked from search entirely.

**How it stayed hidden:** I was calling `memory_search` and getting empty results, but assumed the corpus was just too small. Never verified the index was actually populated. Never tested a known query that SHOULD return results.

**Fix applied:**
- Ran `qmd update` + `qmd embed` — 22 files indexed, 43 vectors
- Changed scope to `default: "allow"` via config patch
- Health check script now verifies qmd index size and runs a test search
- Daily cron re-indexes before running health check

**Lesson:** Always test with a KNOWN query. "Card Plug margin" should return "40%". If it doesn't, search is broken. Don't assume empty results mean "not enough data."

**Never again rule:** The health check script auto-re-indexes if files < 10, and the daily cron re-indexes proactively every morning.

## SOUL.md Rewrite (Feb 9, 2026)

- Complete rewrite from generic template to Ellis-specific identity
- Marco provided business stances via PDF, merged with my operational rules
- Added: interrupt list, team roster, business defaults (product/pricing/marketing/ops)
- Added: "Evolve the team" operating rule
- Removed: "How I Answer" (Marco didn't want rigid answer formatting)
- Weekly Soul Review cron added: Sundays 10 AM, propose changes, Marco approves
