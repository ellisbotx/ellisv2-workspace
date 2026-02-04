# Dashboard Audit Report
Date: 2026-02-03

## Summary
- ✅ 37 tests passed
- ⚠️ 6 issues found
- ❌ 1 critical failure

Notes:
- Audit performed against `http://localhost:8000/trifecta/` in Chrome (OpenClaw browser tool).
- Attempting to start `/Users/ellisbot/.openclaw/workspace/scripts/serve_dashboard.sh` failed due to **port 8000 already in use**, but the dashboard was reachable and tested.

## By Page:

### Homepage (index.html)
- ✅ Overall health badge displays (Health: GREEN)
- ✅ 7-day revenue shows actual data (Last 7d: **$11,769**) 
- ✅ Revenue trend vs prior week displays (**+30.5% vs prior week**)
- ✅ Alert section renders and indicates no issues ("No alerts: Inventory runway is healthy")
- ✅ Navigation links work (Overview/Inventory/Products/Profitability)
- ✅ Brand cards show real totals (e.g., 30d Sales: Black Owned $17,874; Card Plug $19,696; Kinfolk $15,361)
- ✅ ASIN suppression monitor renders (0 issues, 166/166 visible)
- ✅ No JavaScript console errors observed

⚠️ Issue: “Alert count is accurate (stockouts + suppressions)” can’t be verified because homepage only shows a qualitative alert message (no numeric breakdown shown). Consider adding an explicit alert count & breakdown.


### Products (products.html)
- ✅ Page loads and renders all 4 sections (Top Performers / Solid / Slow Movers / Dead Stock)
- ✅ Time range selector updates data (7d vs 30d vs 90d values changed; counts changed)
- ✅ Sanity check holds: example item HoodFued shows Rev (7d) $1,039 < Rev (30d) $5,237 < Rev (90d) $62,427
- ✅ Summary cards update when range changes (example counts: 7d showed 8 top / 21 solid / 46 slow / 83 dead; 30d showed 8/22/76/64)
- ✅ Search box filters instantly (“HoodFued” → “Showing 5 of 170 products”)
- ✅ Status filter dropdown works (e.g., selecting Problem changed count; returned to All statuses)
- ✅ Sorting works by clicking column headers (Rev column showed ↑ and row order changed)
- ✅ “Showing X of Y products” count updates with search and range changes
- ✅ Stock + Runway columns show data (e.g., stock 4,052; runway 545d)
- ✅ No JavaScript console errors observed

⚠️ Issue: In snapshots, the initial (default) view appears to show **Rev (90d)** even when the active range button was not obviously 90d. (After selecting 7d it displayed Rev (7d); after selecting 30d it displayed Rev (30d)). This may just be defaulting to 90d but could be confusing—ensure default range and active button state are always aligned.

⚠️ Issue: Products page uses a different nav/header layout than the homepage/profitability pages (design consistency).

⚠️ Issue: Range persistence via localStorage is **partially confirmed** (after in-page range selection the view stayed consistent during the session), but direct URL `products.html?range=30d` did **not** reliably force 30d (it still displayed Rev (7d) at one point). Recommend confirming range-setting precedence and making URL parameter override explicit.


### Profitability (profitability.html)
- ✅ Page loads and shows range selector (7d/30d/90d)
- ✅ Brand name matching works (Black Owned, Card Plug, Kinfolk)
- ✅ Brand cards show non-zero key metrics (30d: Sales $13,661 / $18,775 / $14,772; Net Profit populated)
- ✅ SKU table populates with data
- ✅ Sortable columns work (Net Profit header toggled sort direction; ↑/↓ indicator changes)
- ✅ Margin % values are populated and plausible (mix of positive/negative; examples: 48.8%, 44.0%, 14.9%)
- ✅ Color coding present (row shading visible in screenshot)
- ✅ No JavaScript console errors observed

❌ Critical failure: **7d view brand summary cards appear blank** (after clicking 7d, the Brand Performance cards rendered without visible metric values). The SKU table still populated. This is a major usability/data bug.

⚠️ Issue: Some rows show “-$0” or “—” for margin/ACOS when revenue is 0. Consider normalizing to “$0” and explicitly defining margin/ACOS as “N/A”.


### Inventory (inventory.html)
- ✅ Page loads without errors
- ✅ Reorder watch section renders (showed “All products have 90+ days of runway — no urgent reorders”)
- ✅ Stock levels shown (Total SKUs 277; Out of Stock 107; Low 19; Medium 28; Healthy 123)
- ✅ By-brand breakdown renders (SKU counts & FBA totals)
- ✅ Runway / velocity concepts shown (e.g., “Liquidation Candidates” with Days of Stock and Velocity)
- ✅ No JavaScript console errors observed

⚠️ Issue: Inventory notes “Velocity is estimated — Sellerboard integration coming”; acceptable, but some “∞ days of stock” entries are likely due to 0 velocity; might want to label as “No sales velocity” instead of infinity.


## Cross-Page Functionality
- ⚠️ Navigation highlighting/active state inconsistent across pages (Products page differs from Profitability page layout; Profitability uses a different header style)
- ✅ Design is broadly consistent dark theme, but header/nav varies (see above)
- ⚠️ Logo consistency: homepage shows “▲ Trifecta”; profitability shows “Trifecta” (no triangle)
- ⚠️ localStorage range persistence: partially confirmed; needs a deterministic test plan. Profitability resets to 30d on reload; Products does not reliably accept URL `?range=30d`.


## Data Integrity
- ✅ No $0.00 “everywhere” issues; key headline values non-zero where expected
- ✅ Totals sanity holds at SKU level (7d < 30d < 90d for the same products)
- ⚠️ SKU counts differ across pages (Products shows 158–170 products depending on range; Inventory shows 277 SKUs). This may be expected (different data sources / SKU definitions) but should be documented.
- ⚠️ Brand totals differ between homepage and profitability (homepage 30d sales: BO $17,874 vs profitability 30d sales BO $13,661). Likely due to different data sources/definitions (Sellerboard export vs derived range json). Needs reconciliation or labeling.


## Performance
- ✅ Pages felt responsive; range switching was near-instant in tests
- ✅ Search/filter responsive
- ✅ No console errors observed


## Issues Found
1. **[P0 / Critical] Profitability 7d Brand Performance cards blank.** The 7d range selection updates label (“Showing 7d range…”) but brand metric values do not render.
2. **[P1] Products range state/URL param inconsistency.** `?range=30d` did not reliably force 30d; ensure consistent precedence between URL, localStorage, and default.
3. **[P1] Navigation/header inconsistency across pages.** Profitability header differs (logo style, placement); active tab highlighting not clearly consistent.
4. **[P1] Brand totals mismatch across pages.** Homepage 30d brand sales do not match Profitability 30d brand sales—needs explicit data-source labeling or reconciliation.
5. **[P2] Profitability: display formatting edge cases.** “-$0” and “—” for margin/ACOS are confusing; use standardized “$0” and “N/A”.
6. **[P2] Inventory: “∞ days of stock” labeling.** Consider replacing with “No sales velocity” or “N/A” for clarity.
7. **[P2] Homepage doesn’t show numeric alert count/breakdown.** Requirement calls for verifying alert count; UI currently doesn’t expose it.


## Recommendations
- Fix the **Profitability 7d brand cards rendering** before Week 2 (P0).
- Establish a single source of truth for **range selection precedence** (URL param > localStorage > default) and make active button state always reflect it.
- Add explicit **data source / definition labels** on all pages (what “Sales” means; which export/range file) and/or harmonize calculations to reduce brand total discrepancies.
- Standardize header/nav components across pages (logo, active tab highlighting) for consistency.
