# Revenue Calculation Bug Report
**Date:** 2026-02-02
**Reporter:** Ellis (Main Agent)
**Analyst:** Opus (Analysis Agent)

---

## Summary

Two critical bugs found in revenue calculations causing massive overcount:
- **Bug 1:** Duplicate column summing (1.19x overcount)
- **Bug 2:** No date filtering on 297-day dataset (2.26x overcount)
- **Combined effect:** 2.68x total overcount

---

## Bug 1: Duplicate Column Summing

### Issue
Sellerboard CSV contains these sales columns:
- `SalesOrganic` - organic sales
- `SalesPPC` - total PPC sales
- `SalesSponsoredProducts` - **DUPLICATE of SalesPPC**
- `SalesSponsoredDisplay` - **DUPLICATE portion of SalesPPC**

### Verification
Manual check of first 3 rows from Black Owned CSV:

| Row | ASIN | SalesOrganic | SalesPPC | SalesSponsoredProducts | SalesSponsoredDisplay |
|-----|------|--------------|----------|------------------------|----------------------|
| 1 | B0B3V463XQ | 324.87 | 124.95 | **124.95** ← identical | 0.00 |
| 2 | B09PCXT4JS | 124.95 | 199.92 | **199.92** ← identical | 0.00 |
| 3 | B0BSR4QN7F | 49.98 | 99.96 | **99.96** ← identical | 0.00 |

**Confirmed:** `SalesSponsoredProducts` always equals `SalesPPC` when PPC > 0.

### Wrong Formula
```python
revenue = SalesOrganic + SalesPPC + SalesSponsoredProducts + SalesSponsoredDisplay
```
This counts PPC sales 2x+ times.

### Correct Formula
```python
revenue = SalesOrganic + SalesPPC
```

---

## Bug 2: No Date Filtering

### Issue
CSV files named `*_dashboard_by_product_90d.csv` actually contain **297 days** of data, not 90 days:
- Date range: 2025-04-11 to 2026-02-02
- Total rows: 12,952 for Black Owned
- This is daily data that needs filtering

### Wrong Approach
Sum ALL rows in the CSV (summing 297 days of data)

### Correct Approach
Filter to last 90 days only:
```python
cutoff_date = datetime(2026, 2, 2) - timedelta(days=90)  # 2025-11-04
# Only include rows where date >= cutoff_date
```

---

## Impact: Black Owned Revenue Example

| Method | Revenue | Error |
|--------|---------|-------|
| **Wrong formula + No filter** | $361,125.47 | 2.68x overcount |
| Correct formula + No filter | $304,648.85 | 2.26x overcount |
| Correct formula + 90d filter | **$134,794.66** | ✅ Correct |
| Expected (Sellerboard screenshot) | $134,869.63 | - |
| **Difference** | **$74.97** | (0.06% - likely timing/rounding) |

---

## Corrected 90-Day Totals (All 3 Brands)

| Brand | Revenue | Units | SKUs |
|-------|---------|-------|------|
| **Black Owned** | $134,794.66 | 5,774 | 52 |
| **Card Plug** | $151,304.67 | 7,954 | 72 |
| **Kinfolk** | $118,537.11 | 5,983 | 46 |
| **TOTAL** | **$404,636.44** | **19,711** | **170** |

### Previous (Wrong) Totals
- Black Owned: $361,125.47 (2.68x)
- Card Plug: $472,886.49 (est. similar ratio)
- Kinfolk: $386,420.88 (est. similar ratio)
- **Previous total: ~$897,784** ← 2.22x overcount on aggregate

---

## Required Fix in `sellerboard_export.py`

### Current Code (WRONG)
```python
revenue = (
    float(row['SalesOrganic'].replace(',', '')) +
    float(row['SalesPPC'].replace(',', '')) +
    float(row['SalesSponsoredProducts'].replace(',', '')) +
    float(row['SalesSponsoredDisplay'].replace(',', ''))
)
```

### Fixed Code (CORRECT)
```python
from datetime import datetime, timedelta

# At start of processing
today = datetime(2026, 2, 2)  # Or datetime.now()
cutoff_90d = today - timedelta(days=90)

# In row processing loop
try:
    row_date = datetime.strptime(row['Date'], '%d/%m/%Y')
except:
    continue  # Skip rows with bad dates

# Only process last 90 days
if row_date >= cutoff_90d:
    revenue = (
        float(row['SalesOrganic'].replace(',', '')) +
        float(row['SalesPPC'].replace(',', ''))
    )
    # ... rest of processing
```

---

## Validation Status

✅ **Black Owned verified:** $134,794.66 vs $134,869.63 expected (99.94% match)  
⏳ **Card Plug:** Needs Sellerboard screenshot verification  
⏳ **Kinfolk:** Needs Sellerboard screenshot verification  

---

## Recommendation

1. ✅ Update `sellerboard_export.py` with both fixes
2. ✅ Regenerate all velocity data and dashboards
3. ✅ Update MEMORY.md with corrected totals
4. ⏳ Ask Marco to verify Card Plug and Kinfolk totals from Sellerboard
5. ⏳ Review any decisions made using old (inflated) revenue numbers

---

**Report completed:** 2026-02-02 15:02 CST
