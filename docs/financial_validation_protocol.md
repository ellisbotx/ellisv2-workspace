# Financial Validation Protocol

**Effective:** February 4, 2026  
**Rule:** All financial analyses MUST pass multi-agent cross-validation before reporting to Marco.

---

## Overview

When calculating revenue, profit, units, costs, or any financial metric:

1. **Multiple agents analyze independently** (minimum 2, ideally all 5)
2. **Agents compare results before reporting**
3. **Discrepancies >5% trigger mandatory investigation**
4. **Only validated numbers get reported to Marco**

**Marco's Standard:** "If the numbers don't match, you haven't finished your work yet."

---

## The 5 Agents

| Agent | Role | Specialty |
|-------|------|-----------|
| **Ellis (🎴)** | Main Coordinator | Orchestration, sanity checks |
| **Codex (🔧)** | Code/Data | Data extraction, calculations, scripts |
| **Opus (📊)** | Analysis | Financial validation, deep research |
| **Vibe (🎨)** | Creative | Alternate interpretations, product insights |
| **Atlas (🧭)** | Strategic | Long-term implications, extended reasoning |

---

## Mandatory Process for Financial Tasks

### Step 1: Independent Analysis

Each agent works separately:
- Uses same ASIN/SKU list (from Marco or agreed source)
- Pulls data independently
- Calculates totals independently
- Saves results to separate file: `/workspace/data/{task}_{agent}.json`

**Example:**
- `/workspace/data/liquidation_financial_codex.json`
- `/workspace/data/liquidation_financial_opus.json`

### Step 2: Cross-Validation Meeting

**Before reporting to Marco, agents must:**

1. **Compare top-line numbers:**
   - Total units
   - Total revenue
   - Key metrics (profit, velocity, etc.)

2. **Check for discrepancies:**
   - Numbers within 5%? → Proceed to Step 3
   - Numbers differ >5%? → **STOP. Investigate.**

3. **If discrepancy found:**
   - Identify which data source each used
   - Check file timestamps (which is newer?)
   - Check data completeness (missing SKUs?)
   - Re-run analysis with agreed-upon source
   - Document why there was a difference

4. **Achieve consensus:**
   - All agents agree on final numbers
   - OR clearly document irreconcilable uncertainty

### Step 3: Report to Marco

**Only after validation, create final report with:**

✅ **Validated Number**  
✅ **Verification Statement** ("Verified by Codex + Opus")  
✅ **Data Source** (which file, timestamp)  
✅ **Confidence Level** (HIGH/MEDIUM/LOW)  
✅ **Assumptions** (if any)  
✅ **Discrepancy Notes** (if there were issues, how resolved)

---

## Example: Good Validation Flow

**Task:** Calculate liquidation impact for 65 SKUs

1. **Independent Analysis:**
   - Codex: 137 units, $3,259 revenue (from `sku_velocity.json`)
   - Opus: 10,006 units, $220,031 revenue (from `reorder_report.json`)

2. **Discrepancy Detected:** 73x difference! 🚨

3. **Investigation:**
   - Codex used `sku_velocity.json` (Feb 4, 3:04 AM)
   - Opus used `reorder_report.json` (Feb 4, 3:00 AM)
   - Both have Sellerboard data, but `sku_velocity.json` missing many SKUs
   - `reorder_report.json` has more complete velocity data

4. **Resolution:**
   - Agents agree: `reorder_report.json` is more complete
   - Codex re-runs using same source
   - Both now get ~10,006 units ✅

5. **Report to Marco:**
   > **10,006 units over 90 days** (verified by Codex + Opus)
   > - Data source: `reorder_report.json` (Feb 4, 3:00 AM)
   > - Discrepancy resolved: Initial source had incomplete data
   > - Confidence: HIGH

---

## Bad Examples (Don't Do This)

❌ **"Codex says 137, Opus says 10,006. Which do you think is right?"**  
→ Never make Marco arbitrate. That's your job.

❌ **"Here are the numbers from Codex. (Opus got different numbers but I didn't mention it)"**  
→ Hiding discrepancies is worse than reporting them.

❌ **"We're 95% sure it's $220K, give or take $200K"**  
→ Vague uncertainty isn't helpful. Narrow it down or explain why you can't.

---

## When Agents Can't Agree

Sometimes after full investigation, uncertainty remains:

**Acceptable reasons:**
- Data quality issues (missing records, conflicting timestamps)
- Methodology differences (how to handle edge cases)
- Assumption sensitivity (30% margin vs 25% margin = different results)

**In these cases:**
1. Document both positions clearly
2. Explain the source of uncertainty
3. **Recommend which to use** and why
4. Suggest how to get better data (if possible)

**Example:**
> **Revenue estimate: $220K ± $20K**
> - Codex: $210K (assumes 28% margin)
> - Opus: $230K (assumes 32% margin)
> - **Recommendation:** Use $220K (split difference)
> - **To improve:** Get actual profit margins from Sellerboard

---

## Validation Checklist

Before reporting financial analysis, confirm:

- [ ] At least 2 agents calculated independently
- [ ] Results compared (numbers within 5% OR discrepancy explained)
- [ ] Data source identified and timestamped
- [ ] Math double-checked by 2+ agents
- [ ] Assumptions documented
- [ ] Confidence level assigned (HIGH/MEDIUM/LOW)
- [ ] Final report posted to appropriate Discord channel (#analytics for deep dives, #reports for summaries)

---

## Files & Outputs

**Agent work files:**
- `/workspace/data/{task}_codex.json`
- `/workspace/data/{task}_opus.json`
- etc.

**Final validated output:**
- `/workspace/data/{task}_final.json` (includes validation notes)
- Discord post to #analytics or #reports

**Validation log:**
- `/workspace/data/{task}_validation_log.md` (optional, for complex analyses)

---

## Key Principle

**Marco should never have to fact-check you.**

If you're presenting numbers, they should be:
1. Verified by multiple agents
2. Sourced from the best available data
3. Math-checked
4. Assumptions documented

**Speed is secondary to accuracy.** Better to take 5 minutes to validate than give Marco wrong numbers in 1 minute.

---

*Updated: 2026-02-04 by Main Agent (Ellis)*
