# Multi-Agent System Guide

**Created:** Feb 2, 2026  
**Status:** Active

---

## Overview

Your OpenClaw system now has **three specialized agents** that work together:

| Agent | Name | Model | Role | Emoji |
|-------|------|-------|------|-------|
| **Main** | Ellis | Claude Sonnet 4.5 | General business operations, daily chat, orchestration | 🎴 |
| **Code** | Codex | OpenAI Codex (gpt-5.2) | Technical work, scripts, automation, debugging | 🔧 |
| **Analysis** | Opus | Claude Opus 4.5 | Deep analysis, research, number validation, reports | 📊 |

**Key Features:**
- All agents share the same workspace → **unified memory and context**
- Agents can message each other to collaborate
- Main agent (Ellis) coordinates complex tasks automatically
- Each agent uses the optimal LLM for its specialty

---

## How It Works

### **Unified Memory**

All three agents read/write to the same files:
- **MEMORY.md** — Long-term knowledge (business rules, preferences, decisions)
- **memory/YYYY-MM-DD.md** — Daily logs (what happened each day)
- **Data files** — Inventory, velocity, reorder reports, etc.

This means:
- Code agent can see what Analysis agent discovered
- Analysis agent can validate what Code agent built
- Ellis (Main) knows everything that happened across all sessions

**You never lose context** when switching between agents.

---

## When to Use Each Agent

### **🎴 Main (Ellis) — Your Default Chat**

**Use for:**
- Daily business check-ins
- General questions
- High-level decisions
- Asking me to coordinate work across agents

**Examples:**
- "What's our inventory status?"
- "Should we liquidate SKU X?"
- "Check if the dashboards are up to date"
- "I have an idea for a new product category — what do you think?"

**When you message Main, I decide:**
- Can I answer this myself? → I respond directly
- Do I need Code's help? → I bring in Code agent
- Do I need Analysis's help? → I bring in Analysis agent
- Do I need both? → I coordinate a collaboration and synthesize the result

---

### **🔧 Code (Codex) — Technical Work**

**Use for:**
- Building or debugging Python scripts
- Implementing automation (Etsy→MCF, Sellerboard exports, etc.)
- Data processing and validation
- API integrations
- Code reviews and optimization

**Examples:**
- "Build a script that does X"
- "Fix the bug in reorder_tracker.py"
- "Automate the Sellerboard export process"
- "Validate that the SKU velocity calculations are correct"

**How Code works:**
- Deep technical focus (doesn't get distracted by business strategy)
- Writes clean, tested code
- Documents everything
- Reports back when done

**You can:**
- Message Code directly (when you know it's a code task)
- Ask Main to bring in Code (I'll coordinate)

---

### **📊 Analysis (Opus) — Deep Dives & Research**

**Use for:**
- SKU performance analysis
- Profitability modeling
- Market research / competitive analysis
- Identifying kill candidates vs growth opportunities
- Validating business decisions with data

**Examples:**
- "Analyze the top 10 SKUs — which ones should we scale?"
- "Research demand for [product category]"
- "Build a profit model for the new product idea"
- "Which SKUs are liquidation candidates based on last 90 days?"

**How Analysis works:**
- Thorough, data-driven analysis
- Questions assumptions
- Runs scenarios and models
- Presents clear recommendations with supporting data

**You can:**
- Message Analysis directly (when you know it's a research/analysis task)
- Ask Main to bring in Analysis (I'll coordinate)

---

## How Agents Collaborate

### **Example 1: You Ask Main a Complex Question**

**You to Main:**  
_"I'm thinking about launching a new card game for Gen Z. What do you think?"_

**What happens behind the scenes:**

1. **Main (Ellis)** thinks: "This needs research + technical feasibility check."
2. **Ellis → Analysis (Opus):**  
   _"Research Gen Z card game market: demand, competition, price points, potential margins."_
3. **Analysis** does deep dive and reports back:  
   _"Market size $X, low competition in niche Y, price sweet spot $15-25, margins 40%+ if we hit 500 units/mo."_
4. **Ellis → Code (Codex):**  
   _"Can we automate fulfillment for a new SKU using existing MCF setup?"_
5. **Code** checks and responds:  
   _"Yes, trivial to add. 10-minute config change."_
6. **Ellis → You (Marco):**  
   _"Analysis says the market looks good (details: [link]). Code confirms fulfillment automation is easy. My take: Worth testing with 1 SKU. Want me to set up the automation and create a tracking dashboard?"_

**You get:**
- Multiple perspectives (market analysis + technical feasibility)
- Cross-validated data
- One clear recommendation

---

### **Example 2: Agents Collaborating Autonomously**

**You to Code:**  
_"Build a new reorder automation script."_

**What happens:**

1. **Code** builds the script
2. **Code → Analysis:**  
   _"I built a reorder script. Can you validate the logic and check if the numbers make sense?"_
3. **Analysis** reviews:  
   _"Logic looks good, but adjust the lead time from 60d to 75d based on supplier history."_
4. **Code** refines the script
5. **Code → You:**  
   _"Script ready. Analysis validated the logic. Lead time set to 75d per their recommendation."_

**You get:**
- Self-correcting system (Code and Analysis cross-check each other)
- Better quality output
- Less manual review needed

---

## How to Message Agents Directly

### **Option A: Let Main Orchestrate (Easiest)**

Just talk to me (Main/Ellis) in this chat. I'll bring in Code or Analysis when needed.

**Example:**
- You: "Can you analyze SKU performance and build a liquidation report?"
- Ellis: "I'll have Analysis review the numbers and Code generate the report."
- *(Ellis coordinates behind the scenes)*
- Ellis: "Report ready: [file path]. Top liquidation candidates: [list]."

---

### **Option B: Message Agents Directly (Advanced)**

For now, you can message agents via CLI while I set up Telegram routing:

```bash
# Send a message to Code agent
openclaw agent --agent code --message "Build X script" --deliver

# Send a message to Analysis agent
openclaw agent --agent analysis --message "Research Y market" --deliver
```

**Coming soon:** I'm working on Telegram group chats where you can message each agent directly from your phone (just like this main chat).

---

## When Should You Use Multiple Agents?

**Use multiple agents when:**
- The task is complex (needs both research AND implementation)
- You want different perspectives (Code's technical view vs Analysis's strategic view)
- You want cross-validation (two agents checking each other's work)
- The work is heavy (offload to specialized agents so Main stays responsive)

**Stick with Main when:**
- Simple questions
- Daily check-ins
- You're not sure which agent to use (I'll route it)

---

## Memory Stays Unified

**Important:** No matter which agent you talk to, memory is shared.

**Example:**
- You tell Code: "The supplier lead time changed to 90 days"
- Code updates a script and logs it in `memory/2026-02-02.md`
- Analysis reads that file later and knows about the lead time change
- Ellis (Main) incorporates it into reorder recommendations

**This means you never have to repeat context** across agents.

---

## Current Status

✅ **Setup Complete:**
- Main agent (Ellis, Claude Sonnet) — active in this chat
- Code agent (Codex, OpenAI) — ready to use
- Analysis agent (Opus, Claude Opus) — ready to use
- Cross-agent messaging enabled
- Shared workspace configured
- MEMORY.md updated with multi-agent system info

🚧 **Coming Soon:**
- Telegram group chats for direct messaging (Code and Analysis)
- Agent routing shortcuts (e.g., "@code build this script")
- Multi-agent collaboration dashboard

---

## Examples of Multi-Agent Workflows

### **Workflow 1: New Product Launch**

**Step 1:** You ask Main: "Should we launch product X?"  
**Step 2:** Ellis brings in Analysis to research market/demand/margins  
**Step 3:** Ellis brings in Code to estimate automation effort  
**Step 4:** Ellis synthesizes both and presents recommendation  

---

### **Workflow 2: Debug + Optimize**

**Step 1:** You notice something off in a script  
**Step 2:** You ask Code: "Fix bug in reorder_tracker.py"  
**Step 3:** Code fixes it and asks Analysis: "Validate the new logic"  
**Step 4:** Analysis confirms it's correct  
**Step 5:** Code reports back to you  

---

### **Workflow 3: Weekly Performance Review**

**Step 1:** Analysis runs a deep SKU performance analysis  
**Step 2:** Analysis identifies top performers and liquidation candidates  
**Step 3:** Analysis sends report to Main  
**Step 4:** Main reviews and messages you: "Here's this week's performance summary"  

---

## Best Practices

1. **Start with Main** — Let Ellis route work to specialized agents
2. **Be specific** — "Analyze SKU X" is better than "check performance"
3. **Trust the collaboration** — Agents will cross-check each other's work
4. **Check MEMORY.md** — Important decisions get documented there automatically
5. **Update memory when context changes** — If supplier lead times change, tell any agent and it gets logged

---

## Troubleshooting

**Q: How do I know which agent I'm talking to?**  
A: Each agent has a distinct emoji in their name:
- 🎴 Ellis (Main)
- 🔧 Codex (Code)
- 📊 Opus (Analysis)

**Q: What if I message the wrong agent?**  
A: No problem — agents can forward messages to each other if needed.

**Q: Do agents see my entire chat history?**  
A: Each agent has its own session, but they all read MEMORY.md and shared files, so they know the important context.

**Q: Can agents work while I'm offline?**  
A: Yes! You can ask Code to "build X overnight" and it'll work + report back when done.

---

## Next Steps

**For now:**
- Keep using this main chat (Ellis) for everything
- I'll automatically bring in Code and Analysis when needed
- Check MEMORY.md to see what gets documented

**Soon (optional):**
- I can set up separate Telegram chats for Code and Analysis
- You can message agents directly from your phone
- Agents can send you proactive alerts

Want me to set up direct Telegram access now, or should we test the collaboration workflow first?

---

*This guide is a living document. As you use the multi-agent system, I'll update it with new workflows and best practices.*
