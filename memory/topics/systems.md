# Systems
*Last updated: 2026-02-10*

---

## Access (Granted/Planned)

| System | Status |
|--------|--------|
| Seller Central (×3) | Read-only — pending setup |
| Sellerboard | Read-only — pending setup |
| Google Sheets | Yes |
| Ad Console | Eventually |
| Supplier comms | Later |

## Tool Stack

- Seller Central (truth) → Sellerboard (profit) → Helium 10 (SEO) → Jungle Scout (demand)
- Google Sheets/Excel for tracking (manual, fragmented)
- No live API pipeline yet

## Discord Channels (18 total)

general, dashboard, inventory, products, automation, analytics, reports, orders, suppliers, creative, finance, done, system, alerts, braindump, growth, tasks, taxes

## Proactive Systems (Feb 8, 2026)

**Marco's mandate:** "Stop asking, start doing." If it benefits the business and I have access, just do it.

**Daily automations (7 AM):** Inventory alerts, sales anomaly detection
**Weekly automations (Mon 7 AM):** Business health report, reorder recommendations
**Daily (9 AM):** Task board update to #tasks

**Task Management System:**
- `/workspace/data/task_tracker.md` — 3 buckets: 🟢 Ellis, 🟡 Marco, 🔴 Blocked
- RULE: Every task posts to #tasks channel. No notification = didn't happen.
- Marco can tell me tasks anywhere — I route to tracker

**Second Brain (#braindump):**
- Ideas vault at `/workspace/data/ideas_vault.md`
- Marco dumps ideas on walks → I capture, research, connect, follow up

**Growth Opportunities (#growth):**
- 27 opportunities tracked at `/workspace/data/growth_opportunities.md`
- Listing optimization, competitor intel, review mining, A+ content, seasonal calendar, etc.

**Accountable Plan Automation (#taxes):**
- $292.54/month × 3 businesses = $877.62/month total reimbursement
- Pay to: Shawnta Grier, Cibolo TX
- 28.5% home office allocation, approved by Marco Grier
- Ellis generates 3 PDFs on 5th of each month → #taxes
- Template locked: `/workspace/data/accountable_plan/template_locked.pdf`

**Wife's Discord Server (pending):**
- Separate server, same bot, own agent profile/personality/memory
- Bot invite: https://discord.com/oauth2/authorize?client_id=1468684601089064962&permissions=412317240384&scope=bot
- On Marco's task list

## Sellerboard Velocity Integration (Completed Feb 2, 2026)

- All 3 brands exported and CORRECTED: Black Owned ($134.5K revenue, 5,763 units), Card Plug ($151.3K, 7,954 units), Kinfolk ($118.5K, 5,983 units)
- Total: 170 SKUs, 19,700 units sold in 90 days, $404,365 revenue (Nov 4, 2025 → Feb 2, 2026, Amazon.com US only)
- Data source: "Dashboard by product" CSV exports from Sellerboard
- Processing script: `/workspace/scripts/sellerboard_export.py`
- Output: `/workspace/data/sku_velocity.json`

## System Reliability Infrastructure (Feb 8, 2026)

- **Gateway Watchdog** — LaunchAgent, every 60s, auto-restarts gateway if down, notifies #alerts. Zero tokens.
- **Cron Health Monitor** — LaunchAgent, every 6h, checks output file freshness, alerts on 2+ consecutive failures. Zero tokens.
- **Update Checker** — LaunchAgent, Sundays 10 AM, checks npm for new OpenClaw versions, notifies #system. Zero tokens.
- All pure scripts — Marco specifically asked these NOT use AI tokens.
- Lesson: Default to token-free scripts for monitoring. Only use agent turns when AI reasoning is actually needed.

## Discord Channel Routing (Feb 4, 2026)

- All automation results route to dedicated channels
- Configuration: `/workspace/config/discord_channels.json`
- Helper module: `/workspace/scripts/discord_utils.py`
- Documentation: `/workspace/docs/discord_routing.md`
- Daily ASIN check → #reports (summary) + #alerts (if suppressions)
- Memory/skill updates → #system
- Etsy→MCF automation → #orders (when implemented)
- Reorder recommendations → #inventory (when implemented)

## LLM Configuration (Updated Feb 11, 2026)

- **Ellis (main): GPT-5.3 Codex (OpenAI)** — changed from Claude Opus 4.6 per Marco's request
- Analysis agent (Opus): Claude Opus 4.6 — kept for cross-validation diversity
- Creative agent (Vibe): Claude Sonnet 4.5
- Strategic agent (Atlas): OpenAI o1
- OpenAI Codex (gpt-5.2) available but not default
- No fallbacks configured (cleaner error messages)
- Cron jobs updated to use Claude Sonnet 4.5 for all scheduled tasks

### FACT System: [2026-02-10 19:38:38 CST] Exec completed... (2026-02-11)
System: [2026-02-10 19:38:38 CST] Exec completed (kind-cor, code 0) :: Score: 38% @@ -44,4 @@ (43 before, 95 after) - Black Owned: 56 SKUs, 15,175 units, $361,125 revenue - Card Plug: 72 SKUs, 14,151 units, $269,187 revenue - Kinfolk: 46 SKUs, 13,421 units, $267,472 revenue qmd://memory-dir/2026-02-04.md #ce9b17 Title: 2026-02-04 Score: 33% @@ -1,3 @@ (0 before, 87 after) # 2026-02-04 ## 20:44 CST — Multi-Agent CSV Validation Complete (Subagent Coordinator)
Tags: kinfolk, card plug, black owned

### FACT System: [2026-02-11 06:37:38 CST] Exec completed... (2026-02-11)
System: [2026-02-11 06:37:38 CST] Exec completed (lucky-ro, code 0) :: CSV Validation Complete (Subagent Coordinator) qmd://memory-dir/2026-02-08.md:33 #d81fbc Title: 2026-02-08 Score: 76% @@ -32,4 @@ (31 before, 76 after) - Daily 9 AM cron posts updated board to #tasks - **RULE:** Every task gets written to file AND posted to #tasks. Discord notification = confirmation it's saved. - Marco can tell me tasks ANYWHERE — I add them to tracker regardless of channel
Tags: marco

### FACT yes, please do this. Let's let's... (2026-02-11)
yes, please do this. Let's let's build as many systems to make this the very best overall system possible let's stop fucking playing if that's gonna get the job done build that shit. This is what I keep telling you if if it's gonna make my life easier and make you more efficient build it. We have a Mac mini here full of all types of space build whatever you need to build to help me get to $5 million. If you can't even tell me what task I asked you to add to the task list then I cannot fucking trust you when you say stop running adsthis shit is getting fucking ridiculous. I'm asking you to take time out and look at ways to improve yourself I have said this look at ways to improve processes. Look at ways to stop fucking forgetting shit this is why I've spent all types of time in the systems channel saying hey how could we make the memory better? How can we make it better constantly work on it. How could we make it better? I've said this over and over and over and over and then you keep saying oh yeah it's working great now it's doing this is doing that same thing but if I ask you to do something, don't forget it write it down get another system do what you said you're gonna do build a validation check that runs every heartbeat. Do what needs to be done to make this to premiere system you can do it. I believe you you got the agents you got the LLM's to do it this shit is ridiculous. Let's fucking do it and give me a clear understanding of what you're doing and what you need to do and what I need to do to help you do it. [from: LewisG (1467288867697590426)]
Tags: ads

### FACT - $50K capital freed + $24-30K/year... (2026-02-11)
- $50K capital freed + $24-30K/year savings = **$74-80K first-year benefit**
Tags: general

### FACT ✅ **Recommendation:** Save 5-6 SKUs, liquidate... (2026-02-11)
✅ **Recommendation:** Save 5-6 SKUs, liquidate 59-60, redeploy $50K capital
Tags: general
