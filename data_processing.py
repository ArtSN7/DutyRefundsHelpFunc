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


def generate_summary_report(df):
    """
    Generate comprehensive summary report

    Args:
        df: Preprocessed DataFrame

    Returns:
        Dictionary with all key metrics
    """
    vat_by_country = calculate_vat_by_country(df)
    returns_revenue = calculate_returns_and_revenue(df)
    total_vat = calculate_total_vat(df)

    summary = {
        'total_vat_paid': total_vat,
        'total_revenue': returns_revenue['DR Revenue'].sum(),
        'vat_by_country': vat_by_country,
        'returns_and_revenue': returns_revenue
    }

    if 'Month' in df.columns:
        summary['monthly_breakdown'] = calculate_monthly_vat_breakdown(df)

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

    # Generate full report
    summary = generate_summary_report(df)

    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)
    print(f"\nTotal VAT Paid on Imports: €{summary['total_vat_paid']:.2f}")
    print(f"Total Company Revenue from Returns: €{summary['total_revenue']:.2f}")

    print("\n\nVAT BY COUNTRY (Net Imports):")
    print(summary['vat_by_country'].to_string(index=False))

    print("\n\nRETURNS & REVENUE BY COUNTRY:")
    print(summary['returns_and_revenue'].to_string(index=False))

    # Print monthly breakdown if available
    if 'monthly_breakdown' in summary:
        print_monthly_report(summary['monthly_breakdown'])
