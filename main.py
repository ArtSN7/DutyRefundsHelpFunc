import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# Загрузка данных
file_path = "data.csv"
df = pd.read_csv(file_path)

# Определение ставок VAT и duty
vat_rates = {
    'DE': 0.19, 'PT': 0.23, 'ES': 0.21, 'IE': 0.23, 'IT': 0.22
}
duty_rates = {
    '6105100000': 0.12, '6110209100': 0.12, '6204629090': 0.12, '6206400000': 0.12,
    '6204430000': 0.12, '6104440000': 0.12, '6203423500': 0.12, '6203310000': 0.12,
    '6215100090': 0.12, '6302100000': 0.12, '7113110000': 0.025, '9503009990': 0.0,
    '6204499090': 0.12, '4202229090': 0.10, '6104430090': 0.12, '6110909000': 0.12,
    '62046318': 0.12, '6204439090': 0.12
}

# Автоматическое определение названий колонок
country_col = next((col for col in df.columns if 'Country' in col or 'country' in col), None)
quantity_col = next((col for col in df.columns if 'Quantity' in col and 'Returned' not in col), None)
quantity_returned_col = next((col for col in df.columns if 'Returned' in col or 'returned' in col), None)
price_col = next((col for col in df.columns if 'Price' in col or 'price' in col), None)
hs_code_col = next((col for col in df.columns if 'HS' in col or 'CODE' in col), None)
parcel_id_col = next((col for col in df.columns if 'Parcel' in col or 'ID' in col or 'Order' in col), None)
item_name_col = next((col for col in df.columns if 'Name' in col or 'Product' in col or 'Item' in col), None)

# Фильтрация EU стран
eu_countries = ['DE', 'PT', 'ES', 'IE', 'IT']
df_eu = df[df[country_col].isin(eu_countries)].copy()

# Обработка пропущенных значений
df_eu[quantity_returned_col] = df_eu[quantity_returned_col].fillna(0)

# ========== РАСЧЕТ ДЛЯ ВСЕХ ПРОДАЖ ==========
df_eu['Quantity Sold'] = df_eu[quantity_col] - df_eu[quantity_returned_col]
df_eu['Total Revenue'] = df_eu[price_col] * df_eu['Quantity Sold']
df_eu['VAT per Unit'] = df_eu.apply(lambda row: row[price_col] * vat_rates.get(row[country_col], 0), axis=1)
df_eu['Duty per Unit'] = df_eu.apply(lambda row: row[price_col] * duty_rates.get(str(row[hs_code_col]), 0), axis=1)
df_eu['Total VAT Paid'] = df_eu['VAT per Unit'] * df_eu['Quantity Sold']
df_eu['Total Duty Paid'] = df_eu['Duty per Unit'] * df_eu['Quantity Sold']

# ========== РАСЧЕТ ДЛЯ ВОЗВРАТОВ ==========
returns_df = df_eu[df_eu[quantity_returned_col] > 0].copy()
returns_df['Return VAT'] = returns_df['VAT per Unit'] * returns_df[quantity_returned_col]
# IE (Ireland) does not allow duty refunds, only VAT refunds
returns_df['Return Duty'] = returns_df.apply(
    lambda row: 0 if row[country_col] == 'IE' else row['Duty per Unit'] * row[quantity_returned_col],
    axis=1
)
returns_df['Total Return Refund'] = returns_df['Return VAT'] + returns_df['Return Duty']
returns_df['Customer Refund (80%)'] = returns_df['Total Return Refund'] * 0.80
returns_df['Our Commission (20%)'] = returns_df['Total Return Refund'] * 0.20

# ========== ИТОГОВАЯ СТАТИСТИКА ==========
print("=" * 80)
print("ОБЩАЯ СТАТИСТИКА ПО ПРОДАЖАМ (EU СТРАНЫ)")
print("=" * 80)
print(f"Всего заказов (EU): {len(df_eu)}")
print(f"Количество проданных единиц: {df_eu['Quantity Sold'].sum():.0f}")
print(f"Общая выручка от продаж: {df_eu['Total Revenue'].sum():,.2f} EUR")
print(f"Общий VAT уплачен: {df_eu['Total VAT Paid'].sum():,.2f} EUR")
print(f"Общий Duty уплачен: {df_eu['Total Duty Paid'].sum():,.2f} EUR")
print(f"Всего VAT + Duty: {(df_eu['Total VAT Paid'].sum() + df_eu['Total Duty Paid'].sum()):,.2f} EUR")

print("\n" + "=" * 80)
print("СТАТИСТИКА ПО ВОЗВРАТАМ")
print("=" * 80)
print(f"Количество возвратов: {len(returns_df)}")
print(f"Единиц возвращено: {returns_df[quantity_returned_col].sum():.0f}")
print(f"Возврат VAT: {returns_df['Return VAT'].sum():,.2f} EUR")
print(f"Возврат Duty: {returns_df['Return Duty'].sum():,.2f} EUR")
print(f"Общая сумма возврата: {returns_df['Total Return Refund'].sum():,.2f} EUR")
print(f"\nВыплата клиентам (80%): {returns_df['Customer Refund (80%)'].sum():,.2f} EUR")
print(f"НАША ПРИБЫЛЬ (20%): {returns_df['Our Commission (20%)'].sum():,.2f} EUR")

print("\n" + "=" * 80)
print("РАЗБИВКА ПО СТРАНАМ")
print("=" * 80)
country_summary = df_eu.groupby(country_col).agg({
    'Total Revenue': 'sum',
    'Total VAT Paid': 'sum',
    'Total Duty Paid': 'sum',
    'Quantity Sold': 'sum'
}).round(2)
print(country_summary)

if len(returns_df) > 0:
    print("ВОЗВРАТЫ ПО СТРАНАМ")
    print("=" * 80)
    returns_by_country = returns_df.groupby(country_col).agg({
        'Our Commission (20%)': 'sum',
        'Customer Refund (80%)': 'sum',
        quantity_returned_col: 'sum'
    }).round(2)
    print(returns_by_country)

# ========== VISUALIZATIONS ==========
print("\n" + "=" * 80)
print("CREATING CHARTS AND GRAPHS...")
print("=" * 80)

# Create a figure with multiple subplots
fig = plt.figure(figsize=(16, 12))

# 1. Revenue by Country (Bar Chart)
plt.subplot(2, 3, 1)
country_revenue = df_eu.groupby(country_col)['Total Revenue'].sum().sort_values(ascending=False)
bars = plt.bar(country_revenue.index, country_revenue.values, color='steelblue', edgecolor='black')
plt.title('Total Revenue by Country', fontsize=12, fontweight='bold')
plt.xlabel('Country')
plt.ylabel('Revenue (EUR)')
plt.xticks(rotation=45)
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'€{height:,.0f}', ha='center', va='bottom', fontsize=9)

# 2. VAT vs Duty Paid by Country (Stacked Bar Chart)
plt.subplot(2, 3, 2)
vat_by_country = df_eu.groupby(country_col)['Total VAT Paid'].sum()
duty_by_country = df_eu.groupby(country_col)['Total Duty Paid'].sum()
x = np.arange(len(vat_by_country))
width = 0.6
p1 = plt.bar(x, vat_by_country.values, width, label='VAT', color='coral')
p2 = plt.bar(x, duty_by_country.values, width, bottom=vat_by_country.values, label='Duty', color='lightseagreen')
plt.title('VAT vs Duty Paid by Country', fontsize=12, fontweight='bold')
plt.xlabel('Country')
plt.ylabel('Amount (EUR)')
plt.xticks(x, vat_by_country.index, rotation=45)
plt.legend()

# 3. Quantity Sold by Country (Pie Chart)
plt.subplot(2, 3, 3)
quantity_by_country = df_eu.groupby(country_col)['Quantity Sold'].sum()
colors = sns.color_palette('pastel')[0:len(quantity_by_country)]
plt.pie(quantity_by_country.values, labels=quantity_by_country.index, autopct='%1.1f%%',
        startangle=90, colors=colors)
plt.title('Quantity Sold Distribution by Country', fontsize=12, fontweight='bold')

# 4. Returns Analysis (if there are returns)
plt.subplot(2, 3, 4)
if len(returns_df) > 0:
    returns_summary = returns_df.groupby(country_col)[quantity_returned_col].sum().sort_values(ascending=False)
    plt.bar(returns_summary.index, returns_summary.values, color='crimson', edgecolor='black')
    plt.title('Returns by Country', fontsize=12, fontweight='bold')
    plt.xlabel('Country')
    plt.ylabel('Units Returned')
    plt.xticks(rotation=45)
else:
    plt.text(0.5, 0.5, 'No Returns Data', ha='center', va='center', fontsize=14)
    plt.title('Returns by Country', fontsize=12, fontweight='bold')
    plt.axis('off')

# 5. Commission Breakdown (Pie Chart)
plt.subplot(2, 3, 5)
if len(returns_df) > 0:
    total_customer_refund = returns_df['Customer Refund (80%)'].sum()
    total_commission = returns_df['Our Commission (20%)'].sum()
    labels = ['Customer Refund (80%)', 'Our Commission (20%)']
    sizes = [total_customer_refund, total_commission]
    colors_pie = ['#ff9999', '#66b3ff']
    explode = (0.05, 0.05)
    plt.pie(sizes, explode=explode, labels=labels, autopct='€%1.0f',
            startangle=90, colors=colors_pie)
    plt.title('Total Refund Distribution', fontsize=12, fontweight='bold')
else:
    plt.text(0.5, 0.5, 'No Returns Data', ha='center', va='center', fontsize=14)
    plt.title('Total Refund Distribution', fontsize=12, fontweight='bold')
    plt.axis('off')

# 6. Overall Financial Summary (Horizontal Bar Chart)
plt.subplot(2, 3, 6)
categories = ['Total Revenue', 'Total VAT', 'Total Duty', 'Total Refunds']
values = [
    df_eu['Total Revenue'].sum(),
    df_eu['Total VAT Paid'].sum(),
    df_eu['Total Duty Paid'].sum(),
    returns_df['Total Return Refund'].sum() if len(returns_df) > 0 else 0
]
colors_bar = ['green', 'orange', 'purple', 'red']
bars = plt.barh(categories, values, color=colors_bar, edgecolor='black')
plt.title('Financial Summary Overview', fontsize=12, fontweight='bold')
plt.xlabel('Amount (EUR)')
for i, bar in enumerate(bars):
    width = bar.get_width()
    plt.text(width, bar.get_y() + bar.get_height()/2.,
             f'€{width:,.0f}', ha='left', va='center', fontsize=9)

plt.tight_layout()
plt.savefig('duty_refunds_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Main dashboard saved as 'duty_refunds_analysis.png'")

# Additional Chart: VAT Rates Comparison
fig2, ax = plt.subplots(1, 2, figsize=(14, 5))

# VAT Rates by Country
ax[0].bar(vat_rates.keys(), [rate * 100 for rate in vat_rates.values()],
          color='skyblue', edgecolor='black')
ax[0].set_title('VAT Rates by Country', fontsize=12, fontweight='bold')
ax[0].set_xlabel('Country')
ax[0].set_ylabel('VAT Rate (%)')
ax[0].set_ylim(0, 25)
for i, (country, rate) in enumerate(vat_rates.items()):
    ax[0].text(i, rate * 100 + 0.5, f'{rate * 100:.0f}%', ha='center', fontweight='bold')

# Top 10 Products by Revenue
ax[1].axis('off')
if item_name_col:
    top_products = df_eu.groupby(item_name_col)['Total Revenue'].sum().sort_values(ascending=False).head(10)
    table_data = []
    for idx, (product, revenue) in enumerate(top_products.items(), 1):
        product_name = product[:30] + '...' if len(str(product)) > 30 else product
        table_data.append([idx, product_name, f'€{revenue:,.2f}'])

    table = ax[1].table(cellText=table_data,
                       colLabels=['#', 'Product Name', 'Revenue'],
                       cellLoc='left',
                       loc='center',
                       colWidths=[0.1, 0.6, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    ax[1].set_title('Top 10 Products by Revenue', fontsize=12, fontweight='bold', pad=20)
else:
    ax[1].text(0.5, 0.5, 'Product name column not found', ha='center', va='center', fontsize=12)
    ax[1].set_title('Top 10 Products by Revenue', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('vat_rates_and_top_products.png', dpi=300, bbox_inches='tight')
print("✓ VAT rates and top products saved as 'vat_rates_and_top_products.png'")

# If there are returns, create a detailed returns chart
if len(returns_df) > 0:
    fig3, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Returns by country - detailed
    ax = axes[0, 0]
    returns_by_country_detailed = returns_df.groupby(country_col).agg({
        'Return VAT': 'sum',
        'Return Duty': 'sum'
    })
    returns_by_country_detailed.plot(kind='bar', ax=ax, color=['coral', 'lightseagreen'])
    ax.set_title('VAT vs Duty Returns by Country', fontsize=12, fontweight='bold')
    ax.set_xlabel('Country')
    ax.set_ylabel('Amount (EUR)')
    ax.legend(['VAT Refund', 'Duty Refund'])
    ax.tick_params(axis='x', rotation=45)

    # Commission by country
    ax = axes[0, 1]
    commission_by_country = returns_df.groupby(country_col)['Our Commission (20%)'].sum().sort_values(ascending=False)
    ax.bar(commission_by_country.index, commission_by_country.values, color='gold', edgecolor='black')
    ax.set_title('Our Commission by Country', fontsize=12, fontweight='bold')
    ax.set_xlabel('Country')
    ax.set_ylabel('Commission (EUR)')
    ax.tick_params(axis='x', rotation=45)
    for i, (country, value) in enumerate(commission_by_country.items()):
        ax.text(i, value, f'€{value:,.0f}', ha='center', va='bottom', fontsize=9)

    # Return rate by country
    ax = axes[1, 0]
    sold_by_country = df_eu.groupby(country_col)['Quantity Sold'].sum()
    returned_by_country = returns_df.groupby(country_col)[quantity_returned_col].sum()
    return_rate = (returned_by_country / (sold_by_country + returned_by_country) * 100).fillna(0)
    ax.bar(return_rate.index, return_rate.values, color='tomato', edgecolor='black')
    ax.set_title('Return Rate by Country', fontsize=12, fontweight='bold')
    ax.set_xlabel('Country')
    ax.set_ylabel('Return Rate (%)')
    ax.tick_params(axis='x', rotation=45)
    for i, (country, value) in enumerate(return_rate.items()):
        ax.text(i, value, f'{value:.1f}%', ha='center', va='bottom', fontsize=9)

    # Customer refund vs Our commission
    ax = axes[1, 1]
    refund_comparison = returns_df.groupby(country_col).agg({
        'Customer Refund (80%)': 'sum',
        'Our Commission (20%)': 'sum'
    })
    refund_comparison.plot(kind='bar', ax=ax, color=['lightcoral', 'lightgreen'])
    ax.set_title('Customer Refund vs Our Commission', fontsize=12, fontweight='bold')
    ax.set_xlabel('Country')
    ax.set_ylabel('Amount (EUR)')
    ax.legend(['Customer Refund', 'Our Commission'])
    ax.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig('returns_detailed_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Detailed returns analysis saved as 'returns_detailed_analysis.png'")

print("\n" + "=" * 80)
print("ALL CHARTS GENERATED SUCCESSFULLY!")
print("=" * 80)
print("\nGenerated files:")
print("  1. duty_refunds_analysis.png - Main dashboard with 6 key charts")
print("  2. vat_rates_and_top_products.png - VAT rates and top products")
if len(returns_df) > 0:
    print("  3. returns_detailed_analysis.png - Detailed returns analysis")
