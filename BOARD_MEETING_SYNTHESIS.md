# Trifecta Dashboard Enhancement - Board Meeting Synthesis
**Date:** February 3, 2026  
**Participants:** All 5 Agents  
**Purpose:** Decide what features to add to the Trifecta dashboard system

---

## Executive Summary

**The Question:** What should we add to the dashboard?

**The Answer:** 6 features in Phase 1 (next 2 weeks), with clear rationale from all 5 perspectives.

**The Decision Framework:** Build features that are (1) technically feasible with current data, (2) statistically sound, (3) UX-friendly, (4) strategically valuable, AND (5) operationally automatable.

---

## 5 Agent Perspectives - Key Themes

### 🧭 Strategic (Atlas): Business Value
- Prioritize **leading indicators** (predict problems) over lagging (report past)
- Focus on **early warning systems** and **decision frameworks**
- Transform dashboard from reporting tool to command center
- **Top picks:** Velocity trends, concentration risk, stockout calendar, cash flow, scorecard

### 🔧 Code (Codex): Technical Feasibility  
- **Critical constraint:** Most features need time-series data (daily historical snapshots)
- Many "Medium" complexity features are actually "High" due to data/architecture needs
- Quick wins exist with current Sellerboard data: concentration, brand comparison, margin trends
- **Reality check:** Alerts, projections, and advanced features require infrastructure upgrades
- **Top picks:** Start with daily snapshot retention system, then build features on top

### 📊 Analysis (Opus): Data Quality & Rigor
- **Major concern:** Weighted scoring creates "false precision" - use transparent decision rules instead
- Statistical significance matters: 20% drop on low-volume SKU is noise, not signal
- Cash flow projections need uncertainty ranges, not single point estimates
- Missing data: lead times, launch dates, historical inventory snapshots
- **Top picks:** Velocity trends (with min volume thresholds), concentration risk, margin erosion

### 🎨 Creative (Vibe): User Experience
- **Design principle:** "Marco gets the answer before he asks the question"
- Mobile-first is non-negotiable - card-based layout beats tables
- **Top picks:** SKU Performance Scorecard (should BE the homepage), Stockout Calendar, Cash Flow Projection
- **Major concerns:** Review tracking, cohort analysis, Buy Box tracking add complexity without value
- **New ideas:** 8 UX features Strategic missed (search/filter, contextual help, comparison mode, notes, morning briefing, celebrations, voice query, undo/history)

### 🎴 Main (Ellis): Operational Workflows
- What enables automated monitoring during heartbeats?
- What reduces need for Marco to manually check things?
- What generates actionable alerts (not just data)?
- What supports the existing nightly automation (ASIN checks, Sellerboard pulls, dashboard regeneration)?
- **Top picks:** Features that can auto-alert proactively: velocity drops, stockout warnings, margin erosion, concentration shifts

---

## Consensus: Phase 1 Features (Next 2 Weeks)

All 5 agents converged on these 6 features for immediate implementation:

### ✅ 1. Daily Snapshot Retention + Time-Series Foundation
**What:** Infrastructure to save daily Sellerboard exports and build time-series from them  
**Why all agents agree:**
- **Strategic:** Enables all trend analysis and projections
- **Code:** Foundation required for 10+ features; do once, use forever
- **Analysis:** Time-series unlocks statistically valid trend detection
- **Creative:** Enables comparison mode and historical views
- **Main:** Powers automated trend monitoring in heartbeats

**Implementation:** 2-3 days  
**Complexity:** Medium (one-time architectural work)

---

### ✅ 2. Revenue Concentration Risk Dashboard
**What:** Show % of revenue from Top 5/10/20 SKUs with risk indicators  
**Why all agents agree:**
- **Strategic:** Critical risk metric for business fragility
- **Code:** Low complexity - pure calculation from existing data
- **Analysis:** Mathematically sound; use Gini coefficient + HHI
- **Creative:** Simple card widget on Cash tab
- **Main:** Can auto-alert if concentration crosses threshold (e.g., >70% in top 5)

**Implementation:** 0.5-1 day  
**Complexity:** Low

---

### ✅ 3. Velocity Trend Analysis (with Statistical Rigor)
**What:** Track velocity trends with arrows (↗↘→) and alerts on significant drops  
**Why all agents agree:**
- **Strategic:** #1 leading indicator for product problems
- **Analysis:** Sound metric IF we add minimum volume thresholds and confidence indicators
- **Code:** Feasible with time-series data
- **Creative:** Arrows + color coding are intuitive on mobile
- **Main:** Enables proactive "Your velocity dropped" alerts

**Implementation:** 2-4 days  
**Complexity:** Medium (needs time-series)  
**Modifications from Strategic's proposal:**
- Add **minimum volume gate**: Only alert if SKU >$500/month AND drops >15%
- Show **confidence badges**: Gray badge = "low volume, high variance"
- Use exponential weighted moving average (EWMA) for responsiveness

---

### ✅ 4. Profit Margin Erosion Alerts
**What:** Track margin changes over time with decomposition (cost vs fee vs price)  
**Why all agents agree:**
- **Strategic:** Catches Amazon's silent fee changes
- **Code:** Low-medium complexity with existing data
- **Analysis:** Fully decomposable - can show WHY margin changed
- **Creative:** Simple alert card on Cash tab
- **Main:** Auto-alert when margin drops >3 percentage points

**Implementation:** 1-2 days  
**Complexity:** Low-Medium

---

### ✅ 5. Brand Performance Comparison
**What:** Side-by-side comparison of Black Owned vs Card Plug vs Kinfolk  
**Why all agents agree:**
- **Strategic:** Shows which brands underperform/overperform
- **Code:** Trivial - just group-by on existing data
- **Analysis:** High insight/effort ratio
- **Creative:** Horizontal bar chart (mobile-friendly)
- **Main:** Enables "Brand X underperforming" alerts

**Implementation:** 0.5-1 day  
**Complexity:** Low

---

### ✅ 6. Mobile-Friendly Homepage Redesign
**What:** Health check dashboard with green/yellow/red status + quick stats  
**Why all agents agree:**
- **Strategic:** First impression matters - health at a glance
- **Code:** Frontend work only, no new data sources
- **Analysis:** Aggregates key metrics into single health score
- **Creative:** THIS is the UX foundation - 5-second health check
- **Main:** The page I'd check during heartbeats to decide if Marco needs alerts

**Design:**
```
┌─────────────────────────────┐
│  TRIFECTA HEALTH CHECK      │
│  ───────────────────────────│
│  💚 All Systems Healthy     │
│                             │
│  📈 Revenue: $38.2K (7d)    │
│     ↗ +8% vs last week      │
│                             │
│  ⚠️  2 stockouts in 14 days │
│  🔴 1 SKU needs attention   │
└─────────────────────────────┘
```

**Implementation:** 1-2 days  
**Complexity:** Low-Medium

---

## Deferred to Phase 2+ (With Modifications)

### 🟡 SKU Performance Scorecard → Needs Rework
**Consensus:** Don't build weighted scoring (false precision)  
**Alternative:** Build **transparent decision rules** instead:
1. Margin <20% → Red flag
2. Velocity declining 3+ weeks → Yellow warning
3. Inventory turns <4x/year → Yellow warning

**Build in:** Phase 2 (after time-series foundation exists)

---

### 🟡 Stockout Risk Calendar → Needs Lead Time Data First
**Consensus:** High value, but **blocked by missing data**  
**Prerequisite:** Add lead time tracking per SKU (manual input initially)  
**Build in:** Phase 2 (after lead time data captured)

---

### 🟡 Cash Flow Projection → Add Uncertainty Ranges
**Consensus:** Don't show single point estimates (false confidence)  
**Modification:** Show **ranges** or **best/worst/likely scenarios**  
**Descope:** 30-day projection only initially (90-day too uncertain)  
**Build in:** Phase 2

---

## Skipped Entirely (Low ROI or Too Complex)

### ❌ Review Velocity Tracking (#10)
- **Creative:** High cost, low actionability
- **Code:** Requires fragile scraping or expensive API
- **Analysis:** Small sample sizes make trends unreliable
- **Decision:** Marco already gets Amazon review alerts; skip this

### ❌ Cohort Analysis (#13)
- **Creative:** "Interesting for analysts, useless for founders"
- **Strategic:** Backward-looking with no forward action
- **Analysis:** Blocked by missing launch date data
- **Decision:** Skip; doesn't pass "so what?" test

### ❌ Buy Box Tracking (#15)
- **Code:** High cost (Keepa subscription) + fragile if scraping
- **Creative:** "Solution to a problem Marco might not have"
- **Analysis:** Not a priority for private label sellers
- **Decision:** Validate Marco actually has Buy Box competition first; likely skip

---

## NEW Features Proposed by Creative Agent

### ✅ Search & Filter (CRITICAL - ADD TO PHASE 1)
**What:** Global search bar + smart filters on SKU list  
**Why:** Essential for scale - what happens when 50+ SKUs?  
**Agreement:** All agents endorse  
**Add to Phase 1:** 1 day of work, huge UX value

### ✅ Time Range Selector (ADD TO PHASE 1)
**What:** Consistent 7/14/30/60/90-day toggle across all pages  
**Why:** Enables trend analysis at different scales  
**Code note:** Easy IF time-series foundation exists  
**Add to Phase 1:** 0.5 day (UI component)

### 🟡 Morning Briefing Notifications (Phase 2)
**What:** 8am push notification with health summary  
**Creative:** "Delight factor" - proactive assistant  
**Main:** Aligns with my heartbeat workflow  
**Decision:** Great idea, build in Phase 2 after alerts infrastructure exists

### 🟡 Contextual Help & Metric Definitions (Phase 2)
**What:** Tap any metric → see plain-language definition  
**Why:** Educational + reduces confusion  
**Decision:** Build in Phase 2 polish

---

## Implementation Plan

### **Week 1 (Days 1-5): Foundation**
1. **Day 1-3:** Build daily snapshot retention system + time-series data structure
2. **Day 4:** Mobile homepage redesign (health check widget)
3. **Day 5:** Search & filter on Products page

**Deliverable:** Infrastructure + improved UX foundation

---

### **Week 2 (Days 6-10): Features**
4. **Day 6:** Revenue Concentration Risk card
5. **Day 7:** Brand Performance Comparison page
6. **Day 8:** Profit Margin Erosion alerts
7. **Day 9-10:** Velocity Trend Analysis (with statistical rigor)

**Deliverable:** 4 new metrics/features live

---

### **After Week 2: Phase 2 Planning**
- Add lead time tracking (prerequisite for stockout calendar)
- Build SKU decision rules (replace scorecard)
- Add morning briefing notifications
- Build cash flow projection (30-day, with ranges)
- Contextual help system

---

## Key Decisions & Principles

### ✅ Agreed By All Agents:

1. **Desktop-first design** - Marco uses this on desktop (mobile is secondary/optional)
2. **Statistical rigor matters** - no false precision, show confidence levels
3. **Leading indicators > lagging** - build what predicts, not just reports
4. **Transparent decision rules > opaque scores** - no black box algorithms
5. **Start with existing data** - don't block on new integrations
6. **Build foundation first** - time-series infrastructure unlocks 10+ features

### ⚠️ Modifications to Strategic's Proposals:

- **SKU Scorecard:** Replace weighted scoring with transparent decision rules
- **Cash Flow:** Add uncertainty ranges, limit to 30-day initially
- **Velocity Alerts:** Add minimum volume thresholds + confidence badges
- **Stockout Calendar:** Defer until lead time data exists

### ❌ Rejected Features:

- Review velocity tracking (high cost, low value)
- Cohort analysis (backward-looking, no action)
- Buy Box tracking (validate need first)

---

## Success Metrics

How do we know Phase 1 worked?

**Usage:**
- Marco checks dashboard daily (currently sporadic)
- Time per session: 2-5 minutes average
- Mobile usage >70%

**Outcomes:**
- Stockout incidents decrease (once calendar built in Phase 2)
- Margin erosion caught within 7 days (not 30)
- Marco asks fewer "how's X looking?" questions in Telegram (data is in dashboard)

**Automation:**
- Ellis (Main Agent) can monitor health during heartbeats
- Automated alerts replace manual checks
- Dashboard becomes "single source of truth"

---

## Final Recommendation to Marco

**Build these 7 features in next 2 weeks:**

1. ✅ Daily snapshot retention + time-series foundation (infrastructure)
2. ✅ Mobile homepage redesign (health check widget)
3. ✅ Search & filter (Products page)
4. ✅ Time range selector (all pages)
5. ✅ Revenue concentration risk
6. ✅ Brand performance comparison
7. ✅ Velocity trend analysis (with stat rigor)
8. ✅ Profit margin erosion alerts

**Phase 2 (after lead time data added):**
- Stockout risk calendar
- SKU decision rules (not scorecard)
- Cash flow projection (30-day with ranges)
- Morning briefing notifications

**Skipped:**
- Review tracking
- Cohort analysis
- Buy Box tracking

---

**Bottom line:** This plan delivers immediate value (Week 1: better UX, Week 2: new insights) while building the foundation for advanced features. All 5 agents agree this is the right sequence.

Ready to implement?

---

*Synthesized by: Main Agent (Ellis)*  
*With input from: Strategic, Code, Analysis, Creative agents*  
*Date: February 3, 2026*
