# Sellerboard Data Inventory

**Date:** 2026-02-03  
**Status:** All automated reports downloading daily

---

## Report Types (8 categories)

### 1. Dashboard by Product
**Location:** `/data/sellerboard/dashboard/`  
**Frequency:** Daily (7-day & 30-day periods)  
**Contains:** Sales, units, profit, margin, ACOS by SKU  
**Files per brand:** 2 (7-day + 30-day)

### 2. Orders
**Location:** `/data/sellerboard/orders/`  
**Frequency:** Daily (7-day & 30-day periods)  
**Contains:** Transaction-level order data  
**Files per brand:** 2 (7-day + 30-day)

### 3. Stock/Inventory
**Location:** `/data/sellerboard/stock/`  
**Frequency:** Daily  
**Contains:** Current inventory levels, warehouse locations  
**Files per brand:** 1

### 4. Cost of Goods Sold (COGS)
**Location:** `/data/sellerboard/cogs/`  
**Frequency:** Daily (7-day period)  
**Contains:** Product costs, landed costs  
**Files per brand:** 1

### 5. Advertising Performance
**Location:** `/data/sellerboard/advertising/`  
**Frequency:** Daily (7-day period)  
**Contains:** Ad spend, impressions, clicks, ACOS by campaign  
**Files per brand:** 1

### 6. FBA Fee Changes
**Location:** `/data/sellerboard/fba_fees/`  
**Frequency:** Daily (30-day period)  
**Contains:** Fee changes, storage fees, fulfillment cost updates  
**Files per brand:** 1

### 7. Other Reports
**Location:** `/data/sellerboard/other/`  
**Frequency:** Varies  
**Contains:** Miscellaneous reports (monthly totals, etc.)  
**Files per brand:** Variable

---

## Total Files

**Per brand:** ~10-12 files daily  
**All 3 brands:** ~30-36 files daily  

**Brands:**
- Black Owned (Summary Dashboard / srgrier45)
- Card Plug  
- Kinfolk

---

## Data Freshness

**Reports available:** Jan 27 - Feb 2, 2026 (7-day)  
**Last updated:** Feb 3, 2026 ~3:00 PM  
**Next update:** Tomorrow (automated daily delivery)

---

## Storage Organization

```
/data/sellerboard/
├── dashboard/          # Sales & profit by SKU
├── orders/             # Transaction details
├── stock/              # Inventory levels
├── cogs/               # Cost tracking
├── advertising/        # Ad performance
├── fba_fees/           # Fee changes
└── other/              # Misc reports
```

---

## Integration Status

**Current dashboards:**
- ✅ Overview (uses dashboard data)
- ✅ Products (uses dashboard data)
- ✅ Profitability (uses dashboard data)
- ✅ Inventory (uses Amazon data)

**To be integrated:**
- ⏳ Orders data
- ⏳ COGS data
- ⏳ Advertising data
- ⏳ FBA fees data
- ⏳ Stock data (combine with Amazon inventory)

**Board meeting in progress** to design integration strategy.
