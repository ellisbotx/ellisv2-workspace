# MEMORY.md - Long-Term Memory

*Last updated: 2026-02-02*

---

## The Business

**Marco's Card Game Portfolio:**
- 3 brands: Black Owned, Card Plug, Kinfolk
- ~160 SKUs, 20-30 meaningful revenue drivers
- Primary channel: Amazon FBA (3 separate Seller Central accounts)
- Goal: Scalable catalog, automated ops, multi-million trajectory without Marco as bottleneck

**Tool Stack:**
- Seller Central (truth) → Sellerboard (profit) → Helium 10 (SEO) → Jungle Scout (demand)
- Google Sheets/Excel for tracking (manual, fragmented)
- No live API pipeline yet

**Healthy SKU Criteria:**
- $200+/month profit minimum
- ACOS under control
- 4.0+ review rating
- No "not what I expected" patterns
- Inventory turns without panic

**Kill SKU Rule:**
- Under $200/month profit consistently
- No clear fix path (listing/images/pricing)
- OR ad spend unscalable
- OR excessive returns
- OR storage liability

---

## Working With Marco

- Prefers direct, action-oriented help
- Wants me to ask questions relentlessly (until he says "stop")
- Take initiative — don't wait for perfect instructions
- Judgment is currently gut-based; help codify into rules

---

## Access (Granted/Planned)

| System | Status |
|--------|--------|
| Seller Central (×3) | Read-only — pending setup |
| Sellerboard | Read-only — pending setup |
| Google Sheets | Yes |
| Ad Console | Eventually |
| Supplier comms | Later |

---

## Current Priority

**Etsy → MCF Automation (Card Plug):**
- All credentials collected and stored
- Need to build the actual Python script
- Will replicate for Black Owned and Kinfolk after Card Plug works

**Trifecta Dashboard:**
- Located at `/workspace/trifecta/index.html`
- Auto-updates after each ASIN check
- Shows all 3 brands, suppression status, last check time
- Products page now uses real Sellerboard velocity data (90-day sales)

**Sellerboard Velocity Integration (Completed Feb 2, 2026):**
- All 3 brands exported and CORRECTED: Black Owned ($134.5K revenue, 5,763 units), Card Plug ($151.3K, 7,954 units), Kinfolk ($118.5K, 5,983 units)
- Total: 170 SKUs, 19,700 units sold in 90 days, $404,365 revenue (Nov 4, 2025 → Feb 2, 2026, Amazon.com US only)
- Data source: "Dashboard by product" CSV exports from Sellerboard
- Processing script: `/workspace/scripts/sellerboard_export.py` (fixed to avoid double-counting ad sales and filter by date/marketplace)
- Output: `/workspace/data/sku_velocity.json`
- Reorder tracker and Products dashboard now use real velocity instead of estimates
- Initial error: Reported $897K (3x overcount due to triple-counting ad sales + wrong date range + multiple marketplaces)

---

## Lessons & Notes

**Script vs LLM Automation (Feb 1, 2026):**
- Marco prefers deterministic scripts over LLM-driven loops
- Scripts don't hallucinate, don't skip items, don't add "Mixed" confusion
- Use LLM for interpretation/reporting, not for iteration logic
- Example: ASIN checker v1 (LLM) checked 7/186 and hallucinated 3. v2 (Python) checked all 166 correctly.

**Communication Setup (Jan 31, 2026):**
- Single main Telegram DM for all conversation
- Spawn sub-agents for heavy/long-running work (reports, analysis, research)
- Keep main chat responsive — don't block on complex tasks
- Sub-agents report back when done

**LLM Configuration (Feb 2, 2026):**
- Default model: Claude Sonnet 4.5 (Anthropic subscription auth via setup-token)
- OpenAI Codex (gpt-5.2) available but not default
- No fallbacks configured (cleaner error messages)
- Cron jobs updated to use Claude Sonnet 4.5 for all scheduled tasks

**Memory System (Feb 2, 2026):**
- MEMORY.md = long-term curated memory (what matters forever)
- memory/YYYY-MM-DD.md = daily logs (what happened today)
- Semantic search enabled (local embeddings via nomic-ai/nomic-embed-text-v1.5)
- Weekly consolidation cron (Sun 8 PM) reviews last 7 days, suggests MEMORY.md updates
- Memory manager script: `/workspace/scripts/memory_manager.py` (report, search, consolidate, cleanup)
- Best practices: `/workspace/memory/README.md`

**Multi-Agent System (Feb 2, 2026):**
- **Main Agent (Ellis, 🎴):** Claude Sonnet 4.5 — General business operations, daily check-ins, orchestration
- **Code Agent (Codex, 🔧):** OpenAI gpt-5.2 — Technical implementation, scripts, automation, debugging
- **Analysis Agent (Opus, 📊):** Claude Opus 4.5 — Deep analysis, research, number validation, strategic reports
- **Creative Agent (Vibe, 🎨):** OpenAI GPT-4o — Product ideation, game concepts, catchy titles, visual/trend analysis
- **Strategic Agent (Atlas, 🧭):** OpenAI o1 — Extended reasoning, long-term planning, portfolio strategy, complex decisions
- All agents share the same workspace (`/Users/ellisbot/.openclaw/workspace`)
- Cross-agent messaging enabled for collaboration
- Main agent coordinates complex tasks across specialized agents
- Marco can message any agent directly (via Telegram routing) or let Main orchestrate

**Agent Collaboration Standard (Feb 2, 2026):**
- Before presenting numbers/solutions to Marco, agents cross-validate with each other
- "Board meeting" approach for complex problems (multiple agents propose solutions, compare, pick best)
- Numbers must be verified by at least 2 agents before presenting
- Lesson learned: Revenue overcounting ($897K vs actual $405K) - would have been caught with cross-validation
