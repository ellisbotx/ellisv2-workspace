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

## LLM Configuration (Feb 2, 2026)

- Default model: Claude Sonnet 4.5 (Anthropic subscription auth via setup-token)
- OpenAI Codex (gpt-5.2) available but not default
- No fallbacks configured (cleaner error messages)
- Cron jobs updated to use Claude Sonnet 4.5 for all scheduled tasks
