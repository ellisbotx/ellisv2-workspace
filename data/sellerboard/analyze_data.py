import csv
import sys
from collections import defaultdict
from datetime import datetime

# Read the CSV
products = defaultdict(lambda: {
    'total_sales': 0,
    'total_units': 0,
    'total_profit': 0,
    'total_ads_spend': 0,
    'days_with_sales': 0,
    'days_in_data': 0,
    'total_fees': 0,
    'total_cogs': 0,
    'dates': set()
})

with open('blackowned_dashboard_by_product_90d_new.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    
    for row in reader:
        asin = row['ASIN'].strip('"')
        name = row['Name'].strip('"')
        date_str = row['Date'].strip('"')
        
        # Parse date
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        except:
            continue
            
        # Add to products
        products[asin]['name'] = name
        products[asin]['dates'].add(date_str)
        products[asin]['days_in_data'] += 1
        
        # Parse numeric fields (handle negatives in parentheses)
        def parse_num(s):
            s = s.strip('"').replace(',', '')
            if not s or s == '':
                return 0
            try:
                return float(s)
            except:
                return 0
        
        sales_organic = parse_num(row['SalesOrganic'])
        sales_ppc = parse_num(row['SalesPPC'])
        units_organic = parse_num(row['UnitsOrganic'])
        units_ppc = parse_num(row['UnitsPPC'])
        net_profit = parse_num(row['NetProfit'])
        ads_spend = parse_num(row['Ads spend'])
        amazon_fees = parse_num(row['AmazonFees'])
        cogs = parse_num(row['Cost of Goods'])
        
        products[asin]['total_sales'] += sales_organic + sales_ppc
        products[asin]['total_units'] += units_organic + units_ppc
        products[asin]['total_profit'] += net_profit
        products[asin]['total_ads_spend'] += abs(ads_spend)  # ads spend is negative
        products[asin]['total_fees'] += abs(amazon_fees)
        products[asin]['total_cogs'] += abs(cogs)
        
        if sales_organic + sales_ppc > 0:
            products[asin]['days_with_sales'] += 1

# Sort by total sales
sorted_products = sorted(products.items(), key=lambda x: x[1]['total_sales'], reverse=True)

# Print top 15 products
print("TOP 15 PRODUCTS BY TOTAL SALES")
print("=" * 120)
print(f"{'ASIN':<15} {'Name':<50} {'Sales':<12} {'Units':<8} {'Profit':<12} {'Margin':<8} {'Days':<6}")
print("=" * 120)

for asin, data in sorted_products[:15]:
    name = data['name'][:47] + "..." if len(data['name']) > 50 else data['name']
    sales = data['total_sales']
    units = data['total_units']
    profit = data['total_profit']
    margin = (profit / sales * 100) if sales > 0 else 0
    days = data['days_with_sales']
    
    print(f"{asin:<15} {name:<50} ${sales:>10.2f} {units:>7.0f} ${profit:>10.2f} {margin:>6.1f}% {days:>5}")

print("\n\nDATA QUALITY CHECKS")
print("=" * 120)

# Check for products with negative margins
neg_margin = [(asin, data) for asin, data in products.items() 
              if data['total_sales'] > 0 and data['total_profit'] < 0]
print(f"\nProducts with negative total profit: {len(neg_margin)}")

if neg_margin:
    print("\nTop 5 money losers:")
    neg_margin.sort(key=lambda x: x[1]['total_profit'])
    for asin, data in neg_margin[:5]:
        print(f"  {asin}: ${data['total_profit']:.2f} profit on ${data['total_sales']:.2f} sales ({data['name'][:60]})")

# Check COGS vs Sales ratios
print("\n\nCOGS ANALYSIS")
for asin, data in sorted_products[:10]:
    if data['total_sales'] > 0:
        cogs_pct = (data['total_cogs'] / data['total_sales']) * 100
        fees_pct = (data['total_fees'] / data['total_sales']) * 100
        ads_pct = (data['total_ads_spend'] / data['total_sales']) * 100
        print(f"{asin}: COGS={cogs_pct:.1f}%, Fees={fees_pct:.1f}%, Ads={ads_pct:.1f}%")

# Date range analysis
all_dates = set()
for data in products.values():
    all_dates.update(data['dates'])

print(f"\n\nDATE RANGE")
print(f"Total unique dates in dataset: {len(all_dates)}")
print(f"Total products: {len(products)}")
print(f"Total rows: {sum(p['days_in_data'] for p in products.values())}")

