# Sellerboard “Dashboard by Product” CSV structure (Sellerboard export)

Source file examined:
- `/workspace/data/sellerboard/blackowned_dashboard_by_product_90d.csv`
- Despite filename suffix `90d`, this particular export contains **30-day** daily rows covering **Jan 3 → Feb 2, 2026**.
  - Evidence: first `Date` value is `03/01/2026` and last is `02/02/2026` (Sellerboard appears to use **DD/MM/YYYY** here).

## What this CSV is
- **Grain:** 1 row per **(Date, Marketplace, ASIN, SKU)**.
- Many rows have zeros (days with no activity), so totals require **summing across the period**.

## Column map (relevant fields)
(1-based column numbers)

Identity / grouping:
1. `Date`
2. `Marketplace`
3. `ASIN`
4. `SKU`
5. `Name`

Sales / revenue (top-line order item sales amounts):
6. `SalesOrganic`
7. `SalesPPC`
8. `SalesSponsoredProducts`
9. `SalesSponsoredDisplay`

Units:
10. `UnitsOrganic`
11. `UnitsPPC`
12. `UnitsSponsoredProducts`
13. `UnitsSponsoredDisplay`

Profit/payout summary (Sellerboard-calculated; not needed for simple unit/revenue totals):
42. `EstimatedPayout`
49. `GrossProfit`
50. `NetProfit`
55. `Ads spend`

Other columns include refunds/fees/costs (e.g., `Refunds`, `Commission`, FBA fees, etc.).

## Key meaning / relationships (important!)
### PPC vs Sponsored Products/Display
In this dataset:
- `UnitsPPC` == `UnitsSponsoredProducts` + `UnitsSponsoredDisplay`
- `SalesPPC` == `SalesSponsoredProducts` + `SalesSponsoredDisplay`
- `UnitsSponsoredDisplay` and `SalesSponsoredDisplay` are **always 0** here.

So **do not double-count** PPC units/sales by adding both `UnitsPPC` and `UnitsSponsoredProducts`.

Interpretation:
- `UnitsPPC`/`SalesPPC` are the **total ad-attributed** units/sales.
- `UnitsSponsoredProducts`/`SalesSponsoredProducts` are a **breakout** of PPC totals by ad type.

### How to compute totals for a date range
For a given ASIN/SKU across a period (sum across all included daily rows):

**Total units sold** (recommended):
- `TotalUnits = sum(UnitsOrganic) + sum(UnitsPPC)`
  - Equivalent (in this file): `sum(UnitsOrganic) + sum(UnitsSponsoredProducts) + sum(UnitsSponsoredDisplay)`

**Total revenue (top-line sales)** (recommended):
- `TotalSales = sum(SalesOrganic) + sum(SalesPPC)`

Notes / caveats:
- These “Sales*” fields are top-line sales amounts; they do **not** automatically net out refunds unless Sellerboard has already adjusted them (refund handling appears elsewhere via dedicated refund/fee columns).
- `Refunds` is a **count** column (integer-ish) in this file, not a dollar value.

## Verification on ASIN example (B09HNH1W74 “Girlll”)
ASIN tested: `B09HNH1W74`

Rows found:
- **32 daily rows** for this ASIN
- Date range present in file for this ASIN:
  - First `Date`: `03/01/2026`
  - Last `Date`: `02/02/2026`

Summed results across those 32 rows:
- `sum(UnitsOrganic)` = **15**
- `sum(UnitsPPC)` = **0**
- `sum(UnitsSponsoredProducts)` = **0**
- `sum(UnitsSponsoredDisplay)` = **0**

Therefore:
- `TotalUnits = 15 + 0 = **15 units**`

Revenue:
- `sum(SalesOrganic)` = **343.86**
- `sum(SalesPPC)` = **0.00**
- `TotalSales = 343.86 + 0.00 = **343.86**`

Sanity check vs expectation:
- Marco saw **38 units** on a **90-day** view; this export (30-day) showing **15 units** is directionally consistent (should be lower).

## Potential edge cases to watch
- **Date parsing:** `03/01/2026` appears to mean **Jan 3, 2026** (DD/MM/YYYY). If any tooling assumes MM/DD/YYYY, periods will look wrong.
- **Other ad types:** The file includes spend columns for `SponsoredВrands` / `SponsoredBrandsVideo`, etc., but **units/sales breakout** columns provided here are only for Sponsored Products + Sponsored Display. If Sellerboard attributes units to SB, they may roll into `UnitsPPC` even if not visible in type-specific unit columns (not observed here, but worth checking on other exports).
- **Refunds:** refund dollars seem to live in other columns (e.g., `Refund Principal`, `Refund Commission`, etc.). Don’t use `Refunds` as a dollar amount.
