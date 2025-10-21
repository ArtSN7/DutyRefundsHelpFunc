import pandas as pd
import numpy as np

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
returns_df['Return Duty'] = returns_df['Duty per Unit'] * returns_df[quantity_returned_col]
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
    print("\n" + "=" * 80)
    print("ДЕТАЛИ ВОЗВРАТОВ")
    print("=" * 80)
    display_cols = [parcel_id_col, item_name_col, country_col, price_col,
                    quantity_returned_col, 'Return VAT', 'Return Duty',
                    'Customer Refund (80%)', 'Our Commission (20%)']
    returns_details = returns_df[display_cols].round(2)
    print(returns_details.to_string(index=False))

    print("\n" + "=" * 80)
    print("ВОЗВРАТЫ ПО СТРАНАМ")
    print("=" * 80)
    returns_by_country = returns_df.groupby(country_col).agg({
        'Our Commission (20%)': 'sum',
        'Customer Refund (80%)': 'sum',
        quantity_returned_col: 'sum'
    }).round(2)
    print(returns_by_country)
