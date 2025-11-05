"""Low value consignment processor (<=150€)."""

import pandas as pd
from typing import Tuple, Any
from config import Config
from services import Services

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class LowValueProcessor:
    """Processes low value consignments (<=150€)."""

    @staticmethod
    def process_low_value_data(df: pd.DataFrame) -> list[Any]:
        """
        Process low value consignment data.

        Returns:
            List containing [DR_revenue, PC_return, total_vat_from_returns, total_import_vat]
        """
        df = LowValueProcessor.clean_columns(df)

        vat_per_country = LowValueProcessor.calculate_vat_per_country(df)
        return_vat_per_country = LowValueProcessor.calculate_return_vat_per_country(df)

        # Calculate DR revenue from low value returns
        DR_revenue, DR_revenue_table = LowValueProcessor.calculate_dr_revenue_from_lw_returns(return_vat_per_country)
        PC_return = return_vat_per_country['Total VAT Refund'].sum() - DR_revenue
        total_import_vat_paid = vat_per_country['Total VAT to Pay'].sum()
        total_vat_needs_to_be_collected_from_returns = return_vat_per_country['Total VAT Refund'].sum()

        # Save reports to CSV files
        Services.store_lv_data(df, vat_per_country, return_vat_per_country, DR_revenue_table)

        return [[DR_revenue, PC_return, total_vat_needs_to_be_collected_from_returns, total_import_vat_paid], [vat_per_country, return_vat_per_country]]

    @staticmethod
    def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Keep only relevant columns for low value consignments."""
        return df[Config.low_value_columns]

    @staticmethod
    def calculate_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT per country."""
        return Services.calculate_vat_per_country(df)

    @staticmethod
    def calculate_return_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT refunds for returned items."""
        return Services.calculate_return_vat_per_country(df)

    @staticmethod
    def calculate_dr_revenue_from_lw_returns(return_vat_per_country: pd.DataFrame) -> Tuple[float, pd.DataFrame]:
        """Calculate DR revenue from low value returns (30% IE, 20% others)."""
        revenue_df = return_vat_per_country.copy()

        # Calculate revenue: 30% for Ireland, 20% for others
        revenue_df['Revenue'] = revenue_df.apply(
            lambda row: row['Total VAT Refund'] * 0.30 if row['Country'] == 'IE'
            else row['Total VAT Refund'] * 0.20,
            axis=1
        )

        # Keep only Country and Revenue columns
        result_df = revenue_df[['Country', 'Revenue']]

        # Calculate total revenue
        total_revenue = result_df['Revenue'].sum()

        return total_revenue, result_df

