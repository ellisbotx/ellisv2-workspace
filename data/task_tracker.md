# ✅ Task Tracker

*Last updated: 2026-02-12*

*Task board pinning disabled per Marco (Feb 12, 2026). Do not pin/unpin task messages in #tasks unless re-enabled.*

---

## 🟢 Ellis Handles (I'll do these)
*Tasks I can complete without Marco. Will report back when done.*

| # | Task | Added | Due | Status |
|---|------|-------|-----|--------|
| 1 | Audit top 10 SKU listings vs category leaders | Feb 8 | Feb 12 | 🟡 In Progress | Kickoff file created: /workspace/data/reports/top10_sku_audit_kickoff_2026-02-12.md |
| 2 | Read all 1-3 star reviews, categorize complaints | Feb 8 | Feb 12 | 🔄 Queued |
| 3 | Build 2026 seasonal promotion calendar | Feb 8 | Feb 14 | 🟡 In Progress | Draft v1 created: /workspace/data/seasonal_promotion_calendar_2026.md |
| 4 | Weekly competitor monitoring | Feb 8 | Weekly | 🔄 Recurring — first report done Feb 10 |
| 5 | Todoist integration setup (connect API token from 1Password, build sync, start hybrid mode) | Feb 12 | Feb 12 | 🟡 In Progress | MVP live + bulk import complete; enabling 5-minute sync cadence per Marco |
| 6 | Todoist ↔ #tasks sync cadence | Feb 12 | — | 🔄 Recurring | 5-minute cadence enabled; reverse-sync backfill active while full #tasks Todoist-first rebuild is underway. |
| 7 | Rebuild #tasks channel for Todoist-first operations (event-driven + clean summaries) | Feb 12 | Feb 12 | 🟡 In Progress | Marco approved ground-up rebuild request in #system. |
| 8 | Implement Execution Escalation Protocol (timeboxes, auto-handoff, proof updates, failure kill switch) | Feb 12 | Feb 12 | 🟡 In Progress | Marco approved in #system. Implementing now. |
| 9 | Upgrade memory health tests to dynamic+rotating suite (not fixed-only) | Feb 12 | Feb 12 | 🟡 In Progress | Marco requested stronger real memory health validation in #system. |
| 5 | Full memory system audit (indexing, capture, recall accuracy, self-heal, model behavior) | Feb 11 | Feb 11 | ✅ Complete | Diagnostic delivered with root-cause attribution |
| 6 | Wire auto-capture into guaranteed conversation ingestion hook | Feb 11 | Feb 11 | ✅ Complete | Added `memory_ingest_from_sessions.py` + cron every 15 min |
| 7 | Add capture-integrity check (conversation vs memory entries) | Feb 11 | Feb 11 | ✅ Complete | Added `memory_capture_integrity.py` + 2-hour cron + report output |
| 8 | Add unknown-then-verify guardrail (no fabricated memory claims) | Feb 11 | Feb 11 | ✅ Complete | Added zero-fabrication guardrail to AGENTS.md |
| 9 | Add memory-miss incident tracker + remediation loop | Feb 11 | Feb 11 | ✅ Complete | Added `memory/memory_miss_incidents.md` + auto-remediation path |
| 10 | Build memory SLO dashboard (latency, miss rate, verification pass rate) | Feb 11 | Feb 11 | ✅ Complete | Added `memory_slo_dashboard.py` + 6:10 AM/PM status cron to #system |
| 11 | Formalize Self-Reflection Protocol (daily mini-review + weekly deep review) | Feb 12 | Feb 12 | ✅ Complete | Protocol doc + 2 cron jobs + AGENTS.md rules added |
| 11 | Full automation integrity audit after model switch (all cron + agents + backups) | Feb 11 | Feb 11 | ✅ Complete | Verified active jobs, force-tested GitHub backup + memory ingestion, fixed failing dashboard reminder cron (disabled) |
| 12 | Implement split-mode operations: Front Desk Ellis + Worker Agents for >2 min tasks | Feb 11 | Feb 11 | ✅ Complete | New default policy: long tasks run in sub-agents; Ellis remains responsive with progress updates every 2-3 minutes. |
| 13 | Execute Discord channel consolidation plan (keep/merge/archive + posting rules) | Feb 11 | Feb 12 | 🟡 In Progress | Marco requested ultra-simple step-by-step ('5th grade level') instructions. Deliver click-by-click instructions and support live while he does it. |
| 14 | Switch #tasks board format to compact change-first layout (no pin flow) | Feb 12 | Next update | ✅ Complete | New format adopted in #tasks and confirmed by Marco ("yes, that looks great"). |
| 15 | Audit Todoist↔#tasks sync and close stale Ellis tasks | Feb 12 | Today | 🟡 In Progress | Verify bidirectional sync integrity, post mismatch list, and mark completed Ellis items done in Todoist + tracker. |

---

## 🟡 Marco Action (Needs you)
*Only Marco can do these. I'll remind and prep.*

| # | Task | Added | Due | Status | Notes |
|---|------|-------|-----|--------|-------|
| 1 | Move ALL liquidation inventory from AWD → FBA, then liquidate | Feb 8 | — | 🔄 In Progress | Master liquidation list updated from Marco message (Feb 11, 2:20 PM) and saved as source of truth for tracking. Includes Black Owned, Kinfolk, and Card Plug ASINs with additions (+1 BO, +2 KF). |
| 2 | Fix Kinfolk Account Health — "At Risk" | Feb 10 | ASAP | 🔄 In Progress | Verifying information requested by Amazon |
| 3 | Family Tree (B0F677914S) — moved to liquidation workflow | Feb 8 | — | ✅ Complete | Closed as standalone CPC task; now tracked under master liquidation workflow. |
| 4 | Just waiting on Black Owned Amazon API | Feb 12 | — | ⏳ Pending | Added from Todoist reverse-sync audit. Waiting for Amazon/SP-API production access enablement. |
| 5 | Test 1017 | Feb 12 | — | ⏳ Pending | Added from Todoist reverse-sync audit. |
| 9 | 🔄 Monthly: Accountable Plan reimbursement update | Feb 8 | 5th of each month | 🔄 Recurring | Ellis generates 3 PDFs (Black Owned, Card Plug, Kinfolk) @ $292.54 each. Posts to #finance. Marco approves & transfers. |
| 14 | 🔄 Monthly: Augusta Rule reimbursement/transfer review | Feb 12 | 25th of each month | 🔄 Recurring | Monthly Augusta Rule check/transfer reminder and confirmation workflow. |
| 10 | Verify accountable plan expense amounts for 2026 | Feb 8 | — | ⏳ Pending | Check last year's amounts, confirm they're still accurate for 2026 |
| 11 | 🔴 TAXES — File by March 15 deadline | Feb 9 | Feb 24 | 🔴 HIGH PRIORITY | Must start working on this by last week of Feb (Feb 23-24). Hard deadline March 15. |
| 12 | Set up Amazon SP-API access (all 3 brands) | Feb 10 | — | ✅ Complete | Card Plug + Kinfolk wired and auth-tested; Black Owned follow-up split to dedicated task. |
| 13 | Ad Change Approval Reviews (3/6/9/14-day checkpoints) | Feb 11 | Feb 24 | 🔄 In Progress | Review cadence: Feb 13, Feb 16, Feb 19, Feb 24. At each checkpoint compare daily units/orders + ad spend impact for: Kinfolk (Hood Hints OG+V2, WSD OG+variation, SayLess OG+SayLess 2, Hood To Hollywood) and Black Owned (Hood Charades all 7 versions). Ellis sends reminder + approval prompt at each checkpoint. |
| 15 | Paperwork (test task) | Feb 12 | Feb 13 | ✅ Complete | Completed by Marco in Todoist (sync verified). |
| 16 | Paperwork number two (test task) | Feb 12 | — | ✅ Complete | Completed by Marco in Todoist (sync verified). |
| 17 | Test this again | Feb 12 | — | ✅ Complete | Completed by Marco in Todoist; synced completion verified. |
| 18 | Test 303 | Feb 12 | — | ✅ Complete | Completed by Marco in Todoist; synced completion verified. |

---

## 🔴 Blocked
*Needs info, access, or a decision.*

| # | Task | Added | Blocker |
|---|------|-------|---------|
| 1 | A+ Content setup | Feb 8 | Brand Registry confirmed ✅ — Ellis can start research/drafts |
| 2 | Supplier management automation | Feb 8 | Needs supplier contacts/pricing |

---

## ✅ Completed
*Done and dusted.*

| # | Task | Completed | Result |
|---|------|-----------|--------|
| 1 | Set up proactive automation (4 scripts) | Feb 8 | ✅ Cron jobs active |
| 2 | Create #braindump channel + ideas vault | Feb 8 | ✅ Live |
| 3 | Create #growth channel + 27 opportunities | Feb 8 | ✅ Live |
| 4 | Create #tasks channel + tracker | Feb 8 | ✅ Live |
| 5 | Liquidation financial analysis (65 SKUs) | Feb 5 | ✅ Posted to #analytics |
| 6 | Update report channel routing to new Discord channel | Feb 11 | ✅ `reports` now points to <#1468684272511746149> |
