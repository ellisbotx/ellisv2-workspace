# Agents
*Last updated: 2026-02-10*

---

## Multi-Agent System (Feb 2, 2026 — updated Feb 8)

- **Main Agent (Ellis, 💰):** Claude Opus 4.6 — General business operations, daily check-ins, orchestration
- **Code Agent (Codex, 🔧):** OpenAI GPT-5.3 Codex — Technical implementation, scripts, automation, debugging
- **Analysis Agent (Opus, 📊):** Claude Opus 4.6 — Deep analysis, research, number validation, strategic reports
- **Creative Agent (Vibe, 🎨):** Claude Sonnet 4.5 — Product ideation, game concepts, catchy titles, visual/trend analysis
- **Strategic Agent (Atlas, 🧭):** OpenAI o1 — Extended reasoning, long-term planning, portfolio strategy, complex decisions
- All agents share the same workspace (`/Users/ellisbot/.openclaw/workspace`)
- Cross-agent messaging enabled for collaboration
- Main agent coordinates complex tasks across specialized agents
- Marco can message any agent directly (via Discord) or let Main orchestrate

## Agent Cross-Validation Protocol (Feb 4, 2026 - MANDATORY)

- **All financial analyses MUST be validated by multiple agents before reporting to Marco**
- Independent analysis: Each agent works separately, saves results to own file
- Cross-validation meeting: Agents compare results, resolve discrepancies >5%
- Only validated numbers get reported (or clear explanation if agents can't agree)
- **Marco's standard:** "If the numbers don't match, you haven't finished your work yet"
- Formal protocol: `/workspace/docs/financial_validation_protocol.md`
- Updated AGENTS.md with mandatory validation rules
- Lesson learned (Feb 4): Codex (137 units) vs Opus (10,006 units) - caught data source issue before reporting final numbers

## Scheduled Tasks Protocol (Feb 5, 2026)

- **SCHEDULED_TASKS.md** tracks all scheduled tasks, completions, and overdue items
- Every heartbeat: review SCHEDULED_TASKS.md for overdue tasks
- If anything overdue: run it immediately or explain why it didn't run
- Log all task completions with timestamp and outcome
- Tasks considered overdue after 2x expected frequency (daily=48h, weekly=14d, hourly=2h)
- Current scheduled tasks:
  - Daily ASIN check (1 AM CST via cron)
  - Weekly memory consolidation (Sun 8 PM CST via cron)
  - Hourly heartbeat proactive checks
- Ensures no tasks slip through the cracks due to cron failures or other issues

## Communication Setup (Jan 31, 2026 → Feb 4, 2026)

- Started with Telegram DM, migrated to Discord (Feb 4)
- Discord server with dedicated channels for different topics
- #general for main conversation
- #alerts for urgent notifications (ASIN suppressions, stockouts, critical issues)
- #reports for daily automation summaries (ASIN checks, performance reports)
- #system for meta updates (memory consolidation, new skills, agent evolution)
- Spawn sub-agents for heavy/long-running work (reports, analysis, research)
- Keep main chat responsive — don't block on complex tasks
- Sub-agents report back when done

### FACT - Codex: 137 units, $3,259 revenue... (2026-02-11)
- Codex: 137 units, $3,259 revenue (used `sku_velocity.json`)
Tags: codex

### FACT - Opus: 10,006 units, $220,031 revenue... (2026-02-11)
- Opus: 10,006 units, $220,031 revenue (used `reorder_report.json`)
Tags: opus

### FACT OK, I think we got a... (2026-02-11)
OK, I think we got a lot of good work done. I think I'm today. I think I'm done for the evening on my briefings. I don't know if they are saying it but I need to know all the automated things that have been done in the morning briefings so if git hub have been performed I need to know. I really need to know all the work that you and the other agents are doing so even if it's repetitive that's fine. I wanna know or somewhere that it has been done but not just to say it has been done. It actually needs to have been completed to be on that morning brief so don't forget those things. [from: LewisG (1467288867697590426)]
Tags: general
Supersedes: prior decision on same topic
