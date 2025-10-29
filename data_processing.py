import pandas as pd
import numpy as np


# Определение ставок VAT и duty
vat_rates = {
    'DE': 0.19,            # Germany
    'PT': 0.23,            # Portugal (mainland, Madeira, Azores)
    'ES': 0.21,            # Spain (except Canary Islands)
    'IE': 0.23,            # Ireland
    'SE': 0.25,            # Sweden
    'NL': 0.21,            # Netherlands
    'DK': 0.25,            # Denmark (mainland only)
    'FI': 0.255,           # Finland (except Åland Islands, raised in 2024)
    'IT': 0.22,            # Italy (except Livigno, Campione d'Italia, Lake Lugano waters)
    'AT': 0.20,            # Austria
    'BE': 0.21,            # Belgium
    'EE': 0.22             # Estonia (until July); use 0.24 for returns post-July 2025
}


def load_and_preprocess_data(csv_path, exclude_non_eu=True):
    """
    Load CSV and preprocess data

    Args:
        csv_path: Path to CSV file
        exclude_non_eu: Whether to exclude non-EU countries

    Returns:
        Preprocessed DataFrame
    """
    df = pd.read_csv(csv_path)

    # Exclude non-EU countries
    if exclude_non_eu:
        df = df[~df['Consignee Country'].isin(['IC', 'CH'])]

    # Clean MRN field, replace any missing MRN with unique parcel ID, so it is treated as separate consignment
    df['MRN'] = df['MRN'].replace(['#N/A', 'N/A', 'NA', 'na', ''], pd.NA)
    df.loc[df['MRN'].isna(), 'MRN'] = df.loc[df['MRN'].isna(), 'Parcel ID']

    # Calculate consignment value
    df['Consignment Value'] = df.groupby('MRN')['Line Item Unit Price'].transform('sum')

    # Map VAT rates
    df['VAT Rate'] = df['Consignee Country'].map(vat_rates)

    # Check for missing VAT rates
    if df['VAT Rate'].isna().any():
        print("WARNING: Some countries missing VAT rates!")
        print(df[df['VAT Rate'].isna()]['Consignee Country'].unique())


    return df


def calculate_vat_by_country(df):
    """
    Calculate VAT paid by country for imported items

    Args:
        df: Preprocessed DataFrame

    Returns:
        DataFrame with VAT calculations by country
    """
    # Calculate net quantity and VAT for all items
    df_copy = df.copy()
    df_copy['Net Quantity'] = df_copy['Line Item Quantity Imported'] - df_copy['Line Item Quantity Returned']
    df_copy['Total Paid'] = df_copy['Net Quantity'] * df_copy['Line Item Unit Price']
    df_copy['VAT Paid'] = df_copy['Total Paid'] * df_copy['VAT Rate']

    # Group by country
    result = df_copy.groupby(['Consignee Country', 'VAT Rate']).agg({
        'VAT Paid': 'sum',
        'Total Paid': 'sum',
        'Net Quantity': 'sum'
    }).reset_index()

    result.columns = ['Country', 'VAT Rate', 'Total VAT Paid', 'Total Items Price', 'Total Quantity']

    return result


def calculate_total_vat(df):
    vat_by_country = calculate_vat_by_country(df)
    return vat_by_country['Total VAT Paid'].sum()


def calculate_returns_and_revenue(df, commission_rate=0.2, ie_commission_rate=0.3):
    """
    Calculate VAT returned and company revenue from returns

    Args:
        df: Preprocessed DataFrame
        commission_rate: Default commission rate (20%)
        ie_commission_rate: Commission rate for Ireland (30%)

    Returns:
        DataFrame with returns and revenue by country
    """
    # Filter only returned items
    df_returns = df[df['Line Item Quantity Returned'] > 0].copy()

    # Calculate VAT on returned items
    df_returns['VAT Returned'] = (
        df_returns['Line Item Quantity Returned'] *
        df_returns['Line Item Unit Price'] *
        df_returns['VAT Rate']
    )

    df_returns['Items Returned Value'] = (
        df_returns['Line Item Quantity Returned'] *
        df_returns['Line Item Unit Price']
    )

    # Group by country
    result = df_returns.groupby(['Consignee Country', 'VAT Rate']).agg({
        'VAT Returned': 'sum',
        'Items Returned Value': 'sum',
        'Line Item Quantity Returned': 'sum'
    }).reset_index()

    # Calculate revenue with different rates for IE
    result['DR Revenue'] = result.apply(
        lambda row: row['VAT Returned'] * (ie_commission_rate if row['Consignee Country'] == 'IE' else commission_rate),
        axis=1
    )

    result.columns = ['Country', 'VAT Rate', 'VAT Returned', 'Items Returned Value', 'Quantity Returned', 'DR Revenue']

    return result


def calculate_monthly_vat_breakdown(df):
    """
    Calculate VAT breakdown by month - imports vs returns

    Args:
        df: Preprocessed DataFrame with 'Month' column

    Returns:
        Dictionary with monthly imports and returns data
    """
    if 'Month' not in df.columns:
        raise ValueError("DataFrame must have a 'Month' column. Ensure dates are parsed.")

    monthly_data = {}

    for month in df['Month'].dropna().unique():
        month_df = df[df['Month'] == month].copy()

        # IMPORTS
        month_df['Imported Quantity'] = month_df['Line Item Quantity Imported']
        month_df['Imported Value'] = month_df['Imported Quantity'] * month_df['Line Item Unit Price']
        month_df['Imported VAT'] = month_df['Imported Value'] * month_df['VAT Rate']

        imports = month_df.groupby(['Consignee Country', 'VAT Rate']).agg({
            'Imported Quantity': 'sum',
            'Imported Value': 'sum',
            'Imported VAT': 'sum'
        }).reset_index()

        # RETURNS
        returns_df = month_df[month_df['Line Item Quantity Returned'] > 0].copy()
        returns_df['Returned Value'] = (
            returns_df['Line Item Quantity Returned'] *
            returns_df['Line Item Unit Price']
        )
        returns_df['Returned VAT'] = returns_df['Returned Value'] * returns_df['VAT Rate']

        returns = returns_df.groupby(['Consignee Country', 'VAT Rate']).agg({
            'Line Item Quantity Returned': 'sum',
            'Returned Value': 'sum',
            'Returned VAT': 'sum'
        }).reset_index()
        returns.columns = ['Country', 'VAT Rate', 'Returned Quantity', 'Returned Value', 'Returned VAT']

        monthly_data[str(month)] = {
            'imports': imports,
            'returns': returns,
            'total_imported_vat': imports['Imported VAT'].sum(),
            'total_returned_vat': returns['Returned VAT'].sum() if not returns.empty else 0
        }

    return monthly_data


def separate_by_consignment_value(df, threshold=150):
    """
    Separate data by consignment value threshold

    Args:
        df: Preprocessed DataFrame
        threshold: Consignment value threshold (default 150)

    Returns:
        Tuple of (df_low, df_high) DataFrames
    """
    df_low = df[df['Consignment Value'] <= threshold].copy()
    df_high = df[df['Consignment Value'] > threshold].copy()

    return df_low, df_high


def calculate_vat_by_consignment_category(df, threshold=150):
    """
    Calculate VAT by country, separated by consignment value

    Args:
        df: Preprocessed DataFrame
        threshold: Consignment value threshold (default 150)

    Returns:
        Dictionary with 'low' and 'high' value DataFrames
    """
    df_low, df_high = separate_by_consignment_value(df, threshold)

    return {
        'low_value': {
            'threshold': f'<=€{threshold}',
            'data': calculate_vat_by_country(df_low),
            'total_vat': calculate_total_vat(df_low),
            'count': len(df_low)
        },
        'high_value': {
            'threshold': f'>€{threshold}',
            'data': calculate_vat_by_country(df_high),
            'total_vat': calculate_total_vat(df_high),
            'count': len(df_high)
        }
    }


def calculate_returns_by_consignment_category(df, threshold=150, commission_rate=0.2, ie_commission_rate=0.3):
    """
    Calculate returns and revenue by consignment value category

    Args:
        df: Preprocessed DataFrame
        threshold: Consignment value threshold (default 150)
        commission_rate: Default commission rate (20%)
        ie_commission_rate: Commission rate for Ireland (30%)

    Returns:
        Dictionary with 'low' and 'high' value DataFrames
    """
    df_low, df_high = separate_by_consignment_value(df, threshold)

    return {
        'low_value': {
            'threshold': f'<=€{threshold}',
            'data': calculate_returns_and_revenue(df_low, commission_rate, ie_commission_rate),
            'total_revenue': calculate_returns_and_revenue(df_low, commission_rate, ie_commission_rate)['DR Revenue'].sum(),
            'count': len(df_low[df_low['Line Item Quantity Returned'] > 0])
        },
        'high_value': {
            'threshold': f'>€{threshold}',
            'data': calculate_returns_and_revenue(df_high, commission_rate, ie_commission_rate),
            'total_revenue': calculate_returns_and_revenue(df_high, commission_rate, ie_commission_rate)['DR Revenue'].sum(),
            'count': len(df_high[df_high['Line Item Quantity Returned'] > 0])
        }
    }


def calculate_monthly_breakdown_by_consignment(df, threshold=150):
    """
    Calculate monthly breakdown separated by consignment value

    Args:
        df: Preprocessed DataFrame with 'Month' column
        threshold: Consignment value threshold (default 150)

    Returns:
        Dictionary with monthly data for each consignment category
    """
    if 'Month' not in df.columns:
        raise ValueError("DataFrame must have a 'Month' column. Ensure dates are parsed.")

    df_low, df_high = separate_by_consignment_value(df, threshold)

    return {
        'low_value': {
            'threshold': f'<=€{threshold}',
            'monthly_data': calculate_monthly_vat_breakdown(df_low)
        },
        'high_value': {
            'threshold': f'>€{threshold}',
            'monthly_data': calculate_monthly_vat_breakdown(df_high)
        }
    }


def generate_summary_report(df, threshold=150):
    """
    Generate comprehensive summary report with consignment value separation

    Args:
        df: Preprocessed DataFrame
        threshold: Consignment value threshold (default 150)

    Returns:
        Dictionary with all key metrics
    """
    vat_by_country = calculate_vat_by_country(df)
    returns_revenue = calculate_returns_and_revenue(df)
    total_vat = calculate_total_vat(df)

    # Add consignment value segmentation
    vat_by_consignment = calculate_vat_by_consignment_category(df, threshold)
    returns_by_consignment = calculate_returns_by_consignment_category(df, threshold)

    summary = {
        'total_vat_paid': total_vat,
        'total_revenue': returns_revenue['DR Revenue'].sum(),
        'vat_by_country': vat_by_country,
        'returns_and_revenue': returns_revenue,
        'vat_by_consignment_value': vat_by_consignment,
        'returns_by_consignment_value': returns_by_consignment
    }

    if 'Month' in df.columns:
        summary['monthly_breakdown'] = calculate_monthly_vat_breakdown(df)
        summary['monthly_by_consignment'] = calculate_monthly_breakdown_by_consignment(df, threshold)

    return summary


def print_monthly_report(monthly_data):
    """
    Print formatted monthly report

    Args:
        monthly_data: Dictionary from calculate_monthly_vat_breakdown
    """
    for month, data in monthly_data.items():
        print(f"\n{'='*80}")
        print(f"MONTH: {month}")
        print(f"{'='*80}")

        print(f"\n📦 IMPORTS:")
        print(f"Total VAT Paid: €{data['total_imported_vat']:.2f}")
        print(data['imports'].to_string(index=False))

        print(f"\n↩️  RETURNS:")
        print(f"Total VAT Returned: €{data['total_returned_vat']:.2f}")
        if not data['returns'].empty:
            print(data['returns'].to_string(index=False))
        else:
            print("No returns this month")


if __name__ == "__main__":
    # Example usage
    csv_path = "TED BAKER DUTY CLAIM BACK Jul-Sep v2.csv"

    # Load and preprocess
    df = load_and_preprocess_data(csv_path)

    # Generate full report with consignment value separation
    summary = generate_summary_report(df, threshold=150)

    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)
    print(f"\nTotal VAT Paid on Imports: €{summary['total_vat_paid']:.2f}")
    print(f"Total Company Revenue from Returns: €{summary['total_revenue']:.2f}")

    print("\n\nVAT BY COUNTRY (Net Imports):")
    print(summary['vat_by_country'].to_string(index=False))

    print("\n\nRETURNS & REVENUE BY COUNTRY:")
    print(summary['returns_and_revenue'].to_string(index=False))

    # Print consignment value breakdown
    print("\n" + "="*80)
    print("BREAKDOWN BY CONSIGNMENT VALUE")
    print("="*80)

    for category in ['low_value', 'high_value']:
        vat_cat = summary['vat_by_consignment_value'][category]
        ret_cat = summary['returns_by_consignment_value'][category]

        print(f"\n{'='*80}")
        print(f"CONSIGNMENT VALUE: {vat_cat['threshold']}")
        print(f"{'='*80}")
        print(f"Total Consignments: {vat_cat['count']}")
        print(f"Total VAT Paid: €{vat_cat['total_vat']:.2f}")
        print(f"Total Returns: {ret_cat['count']}")
        print(f"Total DR Revenue: €{ret_cat['total_revenue']:.2f}")

        print(f"\nVAT by Country ({vat_cat['threshold']}):")
        if not vat_cat['data'].empty:
            print(vat_cat['data'].to_string(index=False))
        else:
            print("No data")

        print(f"\nReturns & Revenue ({ret_cat['threshold']}):")
        if not ret_cat['data'].empty:
            print(ret_cat['data'].to_string(index=False))
        else:
            print("No returns")

    # Print monthly breakdown if available
    if 'monthly_breakdown' in summary:
        print("\n" + "="*80)
        print("MONTHLY BREAKDOWN (ALL CONSIGNMENTS)")
        print("="*80)
        print_monthly_report(summary['monthly_breakdown'])

        # Monthly breakdown by consignment value
        if 'monthly_by_consignment' in summary:
            for category in ['low_value', 'high_value']:
                cat_data = summary['monthly_by_consignment'][category]
                print(f"\n{'='*80}")
                print(f"MONTHLY BREAKDOWN - {cat_data['threshold']}")
                print(f"{'='*80}")
                print_monthly_report(cat_data['monthly_data'])
