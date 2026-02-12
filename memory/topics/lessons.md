# Lessons & Notes
*Last updated: 2026-02-11*

---

## 🔴 CRITICAL: Task Tracker Integrity (Feb 10-11, 2026)

**Problem:** Ellis repeatedly says "Done" when Marco adds/removes tasks but doesn't actually update task_tracker.md. Has happened with:
- PO Box completion (Feb 10) — acknowledged in one channel, still showed on task list hours later, then asked for info already given
- Amazon SP-API (Feb 10) — Marco said "put this on the task list," Ellis said "Done," never wrote to file

**Root cause:** Saying "Done" to Marco feels like completing the task. It isn't. The file edit is the task. Across session boundaries, verbal acknowledgments are lost — only files persist.

**Fix implemented:**
1. Zero-tolerance rule in AGENTS.md: file edit MUST be the very next tool call when a task is mentioned
2. Pin protocol: every change triggers full board refresh (post → unpin old → pin new → update topic)
3. Automated task integrity checker — scans messages vs task_tracker.md every heartbeat
4. Lesson documented in multiple places to survive session resets

**Marco's standard:** "If you can't tell me what tasks I asked you to add, I can't trust you when you say stop running ads." Task management reliability = trust foundation for ALL advice.

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

## Feb 11, 2026 — GitHub Backup Failure (CRITICAL)
- Marco asked 4-5 times for GitHub backup. Ellis confirmed it each time but NEVER ACTUALLY SET UP THE CRON JOB.
- Root cause: git push was silently failing due to a Discord bot token example in DISCORD_MIGRATION_GUIDE.md triggering GitHub's secret scanner. No cron job meant no one noticed.
- **Rule**: "Confirmed" means VERIFIED WORKING. Not "I believe it's set up." Check cron list. Check last run status. Check for errors. If you can't prove it ran, it didn't.
- **Rule**: When setting up git backup, always do a test push immediately. Don't assume it works.

## Feb 11, 2026 — Failed to Log Live Conversation Data

**Problem:** Marco and I ran updated liquidation math in #products (~8 PM Feb 10) with his actual COGS ($1.85/unit, 62,739 units). I never logged it. Next day when he asked about liquidation projections, I pulled stale Mission 3 estimates instead of the numbers we literally calculated together hours earlier. He had to screenshot the conversation to prove it.

**Root cause:** Real-time logging rule exists but wasn't followed for that conversation. The daily log entry for Feb 10 stopped at the memory overhaul and never captured the #products discussion.

**Fix:** Log conversations AS THEY HAPPEN — especially when new numbers supersede old analysis. Update both daily log AND the relevant topic file so search returns current data.

## Feb 11, 2026 — Briefing Data Consistency
- Morning briefing said "0 new orders" in automation section but listed a new order in the orders section. Marco rightfully furious.
- Root cause: overnight order tracker runs in --quiet mode (captures but doesn't notify). Briefing agent read log summaries instead of tracker.json.
- **Rule**: Briefing must read from source-of-truth files (tracker.json), not log summaries. Cross-reference all sections before posting.
- **Rule**: Run a fresh data pull right before briefing time so data is current, not hours old.

### RULE how's the memory going on our... (2026-02-11)
how's the memory going on our system? Is it working out? Do we need to fix anything change anything? Is there any way to expand it to make sure you're learning more and more and I don't have to say things over again. [from: LewisG (1467288867697590426)]
Tags: general

### RULE you know how to fix this... (2026-02-11)
you know how to fix this you should be able to make this the best memory system ever in the history of open claw now tell me what your plan is to fix this. Make sure it's not gonna break anything and tell me who's gonna be responsible in which llm will be making sure it's running properly [from: LewisG (1467288867697590426)]
Tags: general

### RULE is there anything else that needs... (2026-02-11)
is there anything else that needs to be done looking for the full fix? I've asked before and you said oh it's perfect. It's running great no problems and now you're saying that there are problems now. Do we have any checks and balances in place to always be looking for ways to make sure the memory is running a tiptop shape, growing, expanding and easy to utilize for the agents [from: LewisG (1467288867697590426)]
Tags: general

### RULE now also, I've said this before,... (2026-02-11)
now also, I've said this before, but I'm gonna say it again because I don't even know if the memories been working with this being the most important part of this whole entire system if it is not working and it's something I've asked you to make sure it's working then fix it immediately. Don't wait for me to tell you to fix something that I want to be working. Get it fixed if it's something that will make it better then make it better. Don't wait for me now once you do these things I want to know, but it 100% needs to be working 100% of the time. [from: LewisG (1467288867697590426)]
Tags: general

### RULE OK, so Ellis this was before... (2026-02-11)
OK, so Ellis this was before we switched your llm I want you to look at the screenshot and tell me what is wrong with the previous Ellis behavior. [from: LewisG (1467288867697590426)]
Tags: ellis

### RULE OK, so I want you to... (2026-02-11)
OK, so I want you to go through and do a full check on first and foremost the memory of this system I want you to tell me if it's running correctly if there are any updates that need to be done how efficient should it be because I don't know if it's the open claw system or the LLM that I was utilizing that was causing this type of behavior and I want you to take a look at the memory and then we will go from there to See what we need to do know what you need to do to fix this behavior and everything else we got going on give me a full detail [from: LewisG (1467288867697590426)]
Tags: general

### RULE your directive is number one first... (2026-02-11)
your directive is number one first and foremost, memory, memory context, searching of memory. That is the most important thing of this whole open claw system if it doesn't work. Then this is a complete waste of my time so if you know a way to make things better make them work more efficiently, and to help us grow as a company and for you to grow as in as a employee of this company as the person running it as the brain is behind it I want you to automatically do it. Don't ask me just tell me what you have done after it was done here in the systems channel and tell me why it was done that's it so from here on please remember that and get it done so fix those four things and then I'm going to ask you some more questions to find tune in this memory. [from: LewisG (1467288867697590426)]
Tags: general

### RULE OK, so I guess I've always... (2026-02-11)
OK, so I guess I've always looked at this wrong. I've always looked at it as though if the sales is higher than the spin is a good thing, but that's not what you're saying break it down for me on a little bit more basic level. [from: LewisG (1467288867697590426)]
Tags: general

### RULE I really don't even like the... (2026-02-11)
I really don't even like the answer that if it does happen again, I should use something else. Are you not confident in which you can do because confidence is why I'm utilizing you confidence is why I'm listening to you when you tell me to turn ads off and do this and do that if you're not gonna be confident, we can kill this whole thing if you don't believe you can do it we're gonna kill this whole thing if you can't put systems in place that will make sure things like this don't happen, especially after I bring it up then we should just kill this whole thing specially after you said you have to fix and you broke it down line by line what you were gonna do and then after that, you said it won't happen again if it won't happen again, you should've left it at that instead you said if it does and then told me what I should do if it does happen again that's not too reassuring [from: LewisG (1467288867697590426)]
Tags: ads
Supersedes: prior decision on same topic

### RULE exactly lock in because the way... (2026-02-11)
exactly lock in because the way I've been handling business right now. I could keep doing it by myself and say it may not work, but if I got somebody like you, they're supposed to be smarter than me more able than me able to compute and do math better than me be more strategic be less emotional than I need you to login again I have no problems with mess ups. I understand it's gonna have to, but when you tell me you got a fix and then after you in detail, tell me the fix you act as so you might have dropped the ball again that's not locking in. [from: LewisG (1467288867697590426)]
Tags: general

### RULE this is super pissing me off.... (2026-02-11)
this is super pissing me off. I want you to tell me what's wrong with this. Look at the screenshot and then look at this task board and tell me what's wrong and then tell me why does this stuff continue to happen?: [from: LewisG (1467288867697590426)]
Tags: general

### RULE I know this is not what... (2026-02-11)
I know this is not what this channel was for, but tell me what are. The main are the last few issues that we have faced and tell me the fixes that you have implemented to make sure they are good to go. I'm testing this channel. Well to make sure your memory is w and that you can get pulled context from anywhere. [from: LewisG (1467288867697590426)]
Tags: general

### RULE Yes, I want you to implement... (2026-02-11)
Yes, I want you to implement this as a standard practice going forward and make it a formal rule set up validation checkpoints for financial analysis. Anything I have to do with numbers. I wanted to run through all five agents so you can discuss how you get to the numbers if they discrepancies and then come back to me with information that is valid even if it's ran from the wrong number that's fine as long as the numbers match, you have a reason why and then we can figure out if something needs to be shifted. [from: LewisG (1467288867697590426)]
Tags: general

### DIRECTION **Report findings to me via sessions_send.**... (2026-02-11)
**Report findings to me via sessions_send.** Focus on: "Does this story make sense? What's the most likely error?"" just completed successfully.
Tags: general

### FACT **This profile describes slow-to-moderate performers, NOT... (2026-02-11)
**This profile describes slow-to-moderate performers, NOT liquidation candidates.** A product generating $1,100/month in revenue is viable - it's paying for itself and then some. Marco's instinct is correct: you don't liquidate products making money unless something else is broken.
Tags: marco

### FACT **Most likely:** The actual liquidation candidates... (2026-02-11)
**Most likely:** The actual liquidation candidates have <$10K/month total revenue, <$500/month per SKU, and the $220K figure came from matching the wrong ASINs in the analysis.
Tags: general

### FACT **Context:** We reported that 65 liquidation... (2026-02-11)
**Context:** We reported that 65 liquidation SKUs generated $220K in 90 days. Marco said that's wrong - if they made that much, he wouldn't be liquidating them.
Tags: marco

### FACT Marco caught a major error: We... (2026-02-11)
Marco caught a major error: We reported $220K revenue for 65 liquidation SKUs. He correctly said "If they were generating that much, I wouldn't be liquidating them."
Tags: marco

### FACT ## Findings (why the $220K liquidation... (2026-02-11)
## Findings (why the $220K liquidation revenue number is wrong)
Tags: general

### FACT 1. **Hood Charades has a 23.4%... (2026-02-11)
1. **Hood Charades has a 23.4% refund crisis** — Something is fundamentally broken (quality? expectations? packaging?)
Tags: general

### DECISION The data is **solid for pruning... (2026-02-11)
The data is **solid for pruning decisions** (kill the zeros, fix the refunds). For **growth decisions**, you'll want 6-12 months to understand seasonality and lifecycle. But right now? **Trim the fat, fix what's broken, double down on Girls' Night and nostalgia games.**
Tags: general

### FACT 2. **Girlll** - Audit revenue claim... (2026-02-11)
2. **Girlll** - Audit revenue claim ($29K/90d) - if real, major mistake to liquidate
Tags: general

### FACT | Religious games | ❌ NO... (2026-02-11)
| Religious games | ❌ NO | Lost $1,305. Wrong market. |
Tags: general

### DECISION These 65 SKUs taught us valuable... (2026-02-11)
These 65 SKUs taught us valuable lessons about what NOT to do. Now it's time to apply those lessons, cut losses, and double down on what works.
Tags: general

### RULE I want to find a way... (2026-02-11)
I want to find a way to make you the very best assistant possible and I want to find a way for you to be able to automate and take on task without me even telling you to do them. I want to find ways to have you come up with system fixes, and in different things to help my business grow what are the things that you can do are the things that I can do to help you become more proactive without meaning asking which system should we set up and so on [from: LewisG (1467288867697590426)]
Tags: general

### FACT thank you please remember this. This... (2026-02-11)
thank you please remember this. This is how it should be. You see an issue that we've already agreed upon something that should be working. You fixed it. You don't have to check back in with me if it's already something that we have agreed upon remember that. [from: LewisG (1467288867697590426)]
Tags: general

### RULE no, I'm still thinking I should... (2026-02-11)
no, I'm still thinking I should still even though those are the email times at eight noon and seven I probably still should not get an email. If nothing updated those email times should only be used if an update has occurred and I need to fix something in our place in order, but I'm really trying to slim down these times so my brain is not consumed with looking at an email to make sure I get orders in. They will be totally fine if they're done three times a day but again I don't want to email just for fun only if it lead to something I need to accomplish. [from: LewisG (1467288867697590426)]
Tags: general

### RULE you pulled a lot of reports... (2026-02-11)
you pulled a lot of reports today for all three companies. We went through a lot of things I want you to give me a summary of what you learned how you think the business is going and what's most important for the future of the business based off of real information. [from: LewisG (1467288867697590426)]
Tags: general

### COMMITMENT I'm really at this point just... (2026-02-11)
I'm really at this point just testing the memory but give me a high-level overview of each company that you've learned today by going through seller board in Amazon seller Central since this is the finance channel give us a brief synopsis of each of the three companies and then a combined of all three companies [from: LewisG (1467288867697590426)]
Tags: amazon

### RULE I need you to make a... (2026-02-11)
I need you to make a detailed list of the things I need to do to fix the errors that you have found and put those in the task list of course with the most critical acting like such and then you said liquidate all 74 I'm trying to figure out what those 74 ver what I already had on my liquidation list so you need to put a report somewhere maybe in reports of the 74 kill list that you suggest but overall at this information, please remember it taken into a account so we can make it better overall three companies. [from: LewisG (1467288867697590426)]
Tags: general

### RULE So now that we have resetting... (2026-02-11)
So now that we have resetting your brain Ellis to a different llm wants you to verify that all of the automated upgrade systems all of the automated checking everything that should be running on its own. It's still going to be functioning properly and the reason why I say this is because when I switched your brain from another lll of the past, it broke a lot of the systems. So I'm saying that to say I need you to be proactive and change whatever needs to be changed so all systems run correctly [from: LewisG (1467288867697590426)]
Tags: ellis

### FACT System: [2026-02-11 09:20:29 CST] Exec completed... (2026-02-11)
System: [2026-02-11 09:20:29 CST] Exec completed (good-cov, code 0) :: gpt-5.3-codex │ 71k/272k (26%) │ └──────────────────────────────────────────────────────────────┴────────┴─────────┴─────────────────┴─────────────────┘ FAQ: https://docs.openclaw.ai/faq Troubleshooting: https://docs.openclaw.ai/troubleshooting Next steps: Need to share? openclaw status --all Need to debug live? openclaw logs --follow Need to test channels? openclaw status --deep
Tags: codex

### RULE Yes I want you to do... (2026-02-11)
Yes I want you to do this for one side note in 2014. I'm sorry in 2004 no I'm sorry once again. In 2024 we did over 1.3 million 2025 we did over $800,000 so that number of 400k is wrong. I don't know where you got that from but yes, the goal of 5 million in sales is correct [from: LewisG (1467288867697590426)]
Tags: general
