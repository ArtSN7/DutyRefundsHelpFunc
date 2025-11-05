"""High value consignment processor (>150€)."""

import pandas as pd
from typing import Tuple, Any, Dict
from config import Config
from services import Services

import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)



class HighValueProcessor:
    """Processes high value consignments (>150€)."""

    @staticmethod
    def process_high_value_data(df: pd.DataFrame, duty_dict: Dict[str, float]) -> list[Any]:
        """
        Process high value consignment data.

        Args:
            df: High value consignment DataFrame
            duty_dict: Dictionary of duty rates by goods code

        Returns:
            List containing [vat_to_return_from_nl, DR_revenue, vat_difference_txt, vat_to_pay_total]
        """
        df = HighValueProcessor.clean_columns(df)

        # Calculate import VAT that was paid by broker to return from NL
        vat_to_return_from_nl = HighValueProcessor.calculate_vat_to_return_from_nl(df)

        # Calculate VAT per country to submit to NL
        vat_per_country = HighValueProcessor.calculate_vat_per_country(df)
        vat_to_pay_total = vat_per_country['Total VAT to Pay'].sum()

        # Create VAT difference table
        vat_difference_table = HighValueProcessor.create_vat_difference_table(vat_per_country)
        vat_difference_payment_txt = HighValueProcessor.calculate_vat_difference_payment_txt(vat_difference_table)

        # Calculate VAT refunds for returned items
        return_vat_per_country = Services.calculate_return_vat_per_country(df)

        # Getting duty that should be returned for returned items
        return_duty_amount, duty_returned_by_country = HighValueProcessor.calculate_duty_for_returned_items(
            df, duty_dict
        )

        # Merge duty and VAT refunds by country
        combined_refunds = HighValueProcessor.duty_vat_hv_merge(return_vat_per_country, duty_returned_by_country)

        # Calculate DR revenue from high value returns
        DR_revenue_hv, DR_revenue_table = HighValueProcessor.calculate_dr_revenue_from_hw_returns(combined_refunds)

        # Save reports to CSV files
        Services.store_hv_data(df, vat_per_country, vat_difference_table, return_vat_per_country,
                             combined_refunds, DR_revenue_table)

        return [[vat_to_return_from_nl, DR_revenue_hv, vat_difference_payment_txt, vat_to_pay_total], [vat_per_country, duty_returned_by_country, return_vat_per_country]]

    @staticmethod
    def calculate_vat_difference_payment_txt(df: pd.DataFrame) -> str:
        """Calculate VAT difference payment text."""
        vat_in_nl = df['VAT Paid In NL'].sum()
        vat_in_consignee_country = df['VAT Paid In Consignee Country'].sum()
        difference = vat_in_nl - vat_in_consignee_country

        if difference > 0:
            return f'DR needs to return PC an amount of €{difference:.4f} for VAT differences.'
        return f'PC needs to pay DR extra an amount of €{abs(difference):.4f} for VAT differences.'

    @staticmethod
    def create_vat_difference_table(vat_per_country: pd.DataFrame) -> pd.DataFrame:
        """Create VAT difference table comparing NL VAT vs consignee country VAT."""
        vat_difference_table = vat_per_country.copy()

        # Calculate VAT that was paid in NL (21% of consignment value)
        vat_difference_table['VAT Paid In NL'] = vat_difference_table['Total Consignment Value'] * Config.NL_VAT_RATE

        # Rename for clarity
        vat_difference_table = vat_difference_table.rename(columns={
            'Total VAT to Pay': 'VAT Paid In Consignee Country'
        })

        # Reorder columns
        vat_difference_table = vat_difference_table[
            ['Country', 'VAT Rate', 'Total Consignment Value', 'VAT Paid In NL', 'VAT Paid In Consignee Country']]

        return vat_difference_table

    @staticmethod
    def calculate_dr_revenue_from_hw_returns(combined_refunds: pd.DataFrame) -> Tuple[float, pd.DataFrame]:
        """Calculate DR revenue from high value returns (30% IE, 20% others)."""
        revenue_df = combined_refunds.copy()

        # Calculate revenue: 30% for Ireland, 20% for others
        revenue_df['Revenue'] = revenue_df.apply(
            lambda row: row['Total Refund'] * 0.30 if row['Country'] == 'IE'
            else row['Total Refund'] * 0.20,
            axis=1
        )

        # Keep only Country and Revenue columns
        result_df = revenue_df[['Country', 'Revenue']]

        # Calculate total revenue
        total_revenue = result_df['Revenue'].sum()

        return total_revenue, result_df

    @staticmethod
    def duty_vat_hv_merge(vat_df: pd.DataFrame, duty_df: pd.DataFrame) -> pd.DataFrame:
        """Merge VAT and Duty refund dataframes."""
        merged_df = pd.merge(
            vat_df,
            duty_df[['Country', 'Total Duty Returned']],
            on='Country',
            how='outer'
        )

        # Fill NaN with 0
        merged_df = merged_df.fillna({
            'VAT Rate': 0,
            'Total Returned Value': 0,
            'Total VAT Refund': 0,
            'Total Duty Returned': 0
        })

        # Calculate Total Refund (VAT + Duty)
        merged_df['Total Refund'] = merged_df['Total VAT Refund'] + merged_df['Total Duty Returned']

        # Reorder columns
        merged_df = merged_df[[
            'Country', 'VAT Rate', 'Total Returned Value',
            'Total VAT Refund', 'Total Duty Returned', 'Total Refund'
        ]]

        return merged_df

    @staticmethod
    def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Keep only relevant columns for high value consignments."""
        return df[Config.high_value_columns]

    @staticmethod
    def calculate_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT per country."""
        df = df[df['Consignee Country'] != 'NL']  # Exclude NL shipments
        return Services.calculate_vat_per_country(df)

    @staticmethod
    def calculate_duty_for_returned_items(df: pd.DataFrame, duty_dict: Dict[str, float]) -> Tuple[float, pd.DataFrame]:
        """Calculate duty refunds for returned items."""
        returned_df = df[df['Line Item Quantity Returned'] > 0].copy()

        # Extract first 4 digits from HS CODE
        returned_df['Goods_Code_4'] = returned_df['HS CODE'].astype(str).str[:4]

        # Map duty rates
        returned_df['Duty Rate'] = returned_df['Goods_Code_4'].map(duty_dict)

        # Calculate returned value
        returned_df['Returned Item Value'] = (
            returned_df['Line Item Quantity Returned'] *
            returned_df['Line Item Unit Price']
        )

        # Calculate Duty
        returned_df['Duty Amount'] = returned_df['Returned Item Value'] * returned_df['Duty Rate']

        # Group by country
        duty_by_country = returned_df.groupby('Consignee Country').agg({
            'Returned Item Value': 'sum',
            'Duty Amount': 'sum'
        }).reset_index()

        duty_by_country.columns = ['Country', 'Total Returned Value', 'Total Duty Returned']

        total_duty = duty_by_country['Total Duty Returned'].sum()

        return total_duty, duty_by_country

    @staticmethod
    def calculate_vat_to_return_from_nl(df: pd.DataFrame) -> float:
        """Calculate total NL VAT to be returned."""
        unique_consignments = df.drop_duplicates(subset=['MRN'])
        # remove everything shipped to NL, as VAT was already been paid
        unique_consignments = unique_consignments[unique_consignments['Consignee Country'] != 'NL']
        unique_consignments['VAT Amount'] = unique_consignments['Consignment Value'] * Config.NL_VAT_RATE
        total_nl_vat = unique_consignments['VAT Amount'].sum()
        return total_nl_vat

