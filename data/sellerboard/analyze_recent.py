import csv
from datetime import datetime, timedelta
from collections import defaultdict

# Read all data and segregate by time periods
recent_30d = defaultdict(lambda: {'sales': 0, 'units': 0, 'profit': 0, 'days': 0})
recent_60d = defaultdict(lambda: {'sales': 0, 'units': 0, 'profit': 0, 'days': 0})
all_time = defaultdict(lambda: {'sales': 0, 'units': 0, 'profit': 0, 'days': 0, 'name': ''})

# Latest date is Feb 2, 2026
latest_date = datetime(2026, 2, 2)
date_30d_ago = latest_date - timedelta(days=30)
date_60d_ago = latest_date - timedelta(days=60)

with open('blackowned_dashboard_by_product_90d_new.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    
    for row in reader:
        asin = row['ASIN'].strip('"')
        name = row['Name'].strip('"')
        date_str = row['Date'].strip('"')
        
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        except:
            continue
        
        def parse_num(s):
            s = s.strip('"').replace(',', '')
            if not s or s == '':
                return 0
            try:
                return float(s)
            except:
                return 0
        
        sales = parse_num(row['SalesOrganic']) + parse_num(row['SalesPPC'])
        units = parse_num(row['UnitsOrganic']) + parse_num(row['UnitsPPC'])
        profit = parse_num(row['NetProfit'])
        
        # Add to all-time
        all_time[asin]['sales'] += sales
        all_time[asin]['units'] += units
        all_time[asin]['profit'] += profit
        all_time[asin]['days'] += 1
        all_time[asin]['name'] = name
        
        # Add to 60-day if applicable
        if date_obj >= date_60d_ago:
            recent_60d[asin]['sales'] += sales
            recent_60d[asin]['units'] += units
            recent_60d[asin]['profit'] += profit
            recent_60d[asin]['days'] += 1
        
        # Add to 30-day if applicable
        if date_obj >= date_30d_ago:
            recent_30d[asin]['sales'] += sales
            recent_30d[asin]['units'] += units
            recent_30d[asin]['profit'] += profit
            recent_30d[asin]['days'] += 1

print("VELOCITY ANALYSIS: Last 30 Days vs Last 60 Days vs All-Time")
print("=" * 140)
print(f"{'ASIN':<15} {'Product':<45} {'30d Units':<12} {'60d Units':<12} {'All Units':<12} {'Trend':<10}")
print("=" * 140)

# Sort by all-time sales
sorted_all = sorted(all_time.items(), key=lambda x: x[1]['sales'], reverse=True)

for asin, all_data in sorted_all[:20]:
    name = all_data['name'][:42] + "..." if len(all_data['name']) > 45 else all_data['name']
    
    units_30d = recent_30d[asin]['units']
    units_60d = recent_60d[asin]['units']
    units_all = all_data['units']
    
    # Calculate daily averages
    daily_30d = units_30d / 30 if units_30d > 0 else 0
    daily_60d = units_60d / 60 if units_60d > 0 else 0
    daily_all = units_all / all_data['days'] if all_data['days'] > 0 else 0
    
    # Trend
    if daily_30d > daily_60d * 1.1:
        trend = "📈 UP"
    elif daily_30d < daily_60d * 0.9:
        trend = "📉 DOWN"
    elif units_30d == 0:
        trend = "💀 DEAD"
    else:
        trend = "➡️ FLAT"
    
    print(f"{asin:<15} {name:<45} {units_30d:>11.0f} {units_60d:>11.0f} {units_all:>11.0f} {trend:<10}")

print("\n\nWARNING: SLOWEST MOVERS (Last 30 Days)")
print("=" * 100)
print(f"{'ASIN':<15} {'Product':<50} {'30d Units':<10} {'30d Sales':<12}")
print("=" * 100)

# Find products with low recent sales but inventory
slow_movers = []
for asin, all_data in all_time.items():
    units_30d = recent_30d[asin]['units']
    sales_30d = recent_30d[asin]['sales']
    
    # Products with some all-time sales but low/no recent sales
    if all_data['units'] > 20 and units_30d < 10:
        slow_movers.append((asin, all_data, units_30d, sales_30d))

slow_movers.sort(key=lambda x: x[2])  # Sort by 30d units

for asin, all_data, units_30d, sales_30d in slow_movers[:15]:
    name = all_data['name'][:47] + "..." if len(all_data['name']) > 50 else all_data['name']
    print(f"{asin:<15} {name:<50} {units_30d:>9.0f} ${sales_30d:>10.2f}")

print("\n\nSEASONALITY CHECK: Jan 2026 vs Earlier Months")
print("=" * 80)

# Compare January 2026 vs previous months
jan_2026 = defaultdict(lambda: {'sales': 0, 'units': 0})
dec_2025 = defaultdict(lambda: {'sales': 0, 'units': 0})
nov_2025 = defaultdict(lambda: {'sales': 0, 'units': 0})

with open('blackowned_dashboard_by_product_90d_new.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';')
    
    for row in reader:
        asin = row['ASIN'].strip('"')
        date_str = row['Date'].strip('"')
        
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
        except:
            continue
        
        def parse_num(s):
            s = s.strip('"').replace(',', '')
            return float(s) if s and s != '' else 0
        
        sales = parse_num(row['SalesOrganic']) + parse_num(row['SalesPPC'])
        units = parse_num(row['UnitsOrganic']) + parse_num(row['UnitsPPC'])
        
        if date_obj.year == 2026 and date_obj.month == 1:
            jan_2026[asin]['sales'] += sales
            jan_2026[asin]['units'] += units
        elif date_obj.year == 2025 and date_obj.month == 12:
            dec_2025[asin]['sales'] += sales
            dec_2025[asin]['units'] += units
        elif date_obj.year == 2025 and date_obj.month == 11:
            nov_2025[asin]['sales'] += sales
            nov_2025[asin]['units'] += units

# Total comparison
total_jan = sum(d['sales'] for d in jan_2026.values())
total_dec = sum(d['sales'] for d in dec_2025.values())
total_nov = sum(d['sales'] for d in nov_2025.values())

print(f"January 2026 total sales: ${total_jan:,.2f}")
print(f"December 2025 total sales: ${total_dec:,.2f}")
print(f"November 2025 total sales: ${total_nov:,.2f}")
print(f"\nJan vs Dec: {((total_jan/total_dec - 1) * 100):+.1f}%")
print(f"Jan vs Nov: {((total_jan/total_nov - 1) * 100):+.1f}%")

