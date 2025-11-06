"""Shared services for VAT calculations and data storage."""

import pandas as pd
from pathlib import Path
import os
from config import Config

import warnings

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class Services:
    """Shared service methods used across processors."""

    @staticmethod
    def store_lv_data(lv_vat_per_country, lv_return_vat_per_country) -> None:
        """Save low value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        lv_vat_per_country.to_excel(data_dir / "lv_imported_vat_per_country_summary.xlsx", index=False,
                                    engine='openpyxl')
        lv_return_vat_per_country.to_excel(data_dir / "lv_returned_vat_per_country_summary.xlsx", index=False,
                                           engine='openpyxl')

    @staticmethod
    def store_hv_data(hv_vat_per_country, hv_combined_refunds) -> None:
        """Save high value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        hv_vat_per_country.to_excel(data_dir / "hv_imported_vat_per_country_summary.xlsx", index=False,
                                    engine='openpyxl')
        hv_combined_refunds.to_excel(data_dir / "hv_duty_and_vat_returned_values_summary.xlsx", index=False,
                                     engine='openpyxl')

    @staticmethod
    def calculate_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate total VAT to pay per country."""
        # Get unique MRN records (to avoid counting same consignment multiple times)
        unique_consignments = df.drop_duplicates(subset=['MRN'])

        # Calculate VAT amount for each consignment
        unique_consignments['VAT Amount'] = unique_consignments['Consignment Value'] * unique_consignments['VAT Rate']

        # Group by Country and VAT Rate
        summary = unique_consignments.groupby(['Consignee Country', 'VAT Rate']).agg({
            'Consignment Value': 'sum',
            'VAT Amount': 'sum'
        }).reset_index()

        # Rename columns for clarity
        summary.columns = ['Country', 'VAT Rate', 'Total Consignment Value', 'Total VAT to Pay']

        return summary

    @staticmethod
    def calculate_return_vat_per_country(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate VAT refunds for returned items per country."""
        # Filter rows where items were returned
        returned_df = df[df['Line Item Quantity Returned'] > 0].copy()

        # Calculate total returned value for each line item
        returned_df['Returned Item Value'] = (
                returned_df['Line Item Quantity Returned'] *
                returned_df['Line Item Unit Price']
        )

        # Calculate VAT refund for each returned item
        returned_df['VAT Refund'] = returned_df['Returned Item Value'] * returned_df['VAT Rate']

        # Group by Country and VAT Rate
        summary = returned_df.groupby(['Consignee Country', 'VAT Rate']).agg({
            'Returned Item Value': 'sum',
            'VAT Refund': 'sum'
        }).reset_index()

        # Rename columns for clarity
        summary.columns = ['Country', 'VAT Rate', 'Total Returned Value', 'Total VAT Refund']

        return summary


    @staticmethod
    def create_revenue_table(df: pd.DataFrame, lv_df: pd.DataFrame) -> float:
        # Apply commission rates to main df
        df['DR fee rate'] = df['Country'].apply(
            lambda x: Config.IE_COMMISSION_RATE if x == 'IE' else Config.DEFAULT_COMMISSION_RATE)
        df['DR fee'] = (df['Total Refund'] * df['DR fee rate'])

        # Apply commission rates to lv_df
        lv_df['DR fee rate'] = lv_df['Country'].apply(
            lambda x: Config.IE_COMMISSION_RATE if x == 'IE' else Config.DEFAULT_COMMISSION_RATE)

        # Calculate VAT Refund for lv_df (since it doesn't have Total Refund column)
        lv_df['Total Refund'] = lv_df['Total VAT Refund']  # Only VAT refund, no duty
        lv_df['DR fee'] = (lv_df['Total Refund'] * lv_df['DR fee rate'])

        # Merge the dataframes
        # Since lv_df has fewer columns, align them first
        lv_df_aligned = lv_df[['Country', 'VAT Rate', 'Total Returned Value', 'Total VAT Refund']].copy()
        lv_df_aligned['Total Duty Returned'] = 0  # No duty in lv_df
        lv_df_aligned['Total Refund'] = lv_df_aligned['Total VAT Refund']
        lv_df_aligned['DR fee rate'] = lv_df['DR fee rate']
        lv_df_aligned['DR fee'] = lv_df['DR fee']

        # Concatenate both dataframes
        combined_df = pd.concat([df, lv_df_aligned], ignore_index=True)

        # Save to Excel
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)
        combined_df.to_excel(data_dir / "duty_refunds_revenue_summary.xlsx", index=False, engine='openpyxl')

        # Calculate total revenue from both dataframes
        total_dr_revenue = combined_df['DR fee'].sum()

        return total_dr_revenue

    @staticmethod
    def generate_summary_table(data: dict):
        # Calculate all components
        ioss_sales, ioss_vat_to_return = Services.calculate_lv_data(
            data['VAT per Country DataFrame for LV:'],
            data['Return VAT per Country DataFrame for LV:']
        )

        # Calculate NL VAT returns from HV data for parcels that stayed in NL and were returned
        nl_vat_returns = Services.calculate_nl_vat_returns(
            data['Combined Refunds DataFrame for HV:']
        )

        hv_broker_paid = data['VAT Broker Paid During Import in NL for HV:']
        broker_hv_vat_return_nl = data['VAT to Return from NL for HV parcels that didnt stay in NL:']
        hv_oss_import_vat = Services.calculate_oss_vat_payment(
            data['VAT per Country DataFrame for HV:']
        )
        hv_oss_return_vat = Services.calculate_oss_vat_returns(
            data['Combined Refunds DataFrame for HV:']
        )

        # Get totals from Combined Refunds
        total_vat_refund = data['Combined Refunds DataFrame for HV:']['Total VAT Refund'].sum()
        total_duty_returned = data['Combined Refunds DataFrame for HV:']['Total Duty Returned'].sum()

        dr_revenue = data['Total DR Revenue from Refunds:']

        # ✅ CORRECT FORMULAS:

        # Pro Carrier PAYS YOU:
        # 1. Net IOSS VAT (you pay on their behalf)
        # 2. Net OSS VAT (you pay on their behalf)
        # 3. Your commission
        # 4. Adjust for VAT difference (if any)
        invoice_amount = (
                (ioss_sales - ioss_vat_to_return) +  # Net IOSS
                (hv_oss_import_vat - hv_oss_return_vat) -  # Net OSS
                nl_vat_returns +  # minus HV NL VAT Return
                dr_revenue  # Commission
        )

        # DR PAY BACK to Pro Carrier:
        # All refunds from VAT are reducing overall amount DR invoices to Pro Carrier
        # Duty refunds are fully paid back to PC
        # We also need to return reclaimed from broker's payment VAT for HV NL returns
        pc_return_amount = total_duty_returned + broker_hv_vat_return_nl


        rows = [
            ("TOTAL IOSS VAT", ioss_sales, "Total IOSS VAT for sales"),
            ("RETURNED IOSS VAT", ioss_vat_to_return, "IOSS VAT for returns"),
            ("NET IOSS VAT", ioss_sales - ioss_vat_to_return, "Net IOSS position"),
            ("HV NL VAT Return", nl_vat_returns, "Total VAT to return from NL for HV parcels that stayed in NL and were returned"),
            (" ", " ", " "),
            ("AMOUNT BROKER PAID", hv_broker_paid, "VAT paid by broker during import in NL for HV"),
            ("AMOUNT THAT CAN BE CLAIMED BACK", broker_hv_vat_return_nl, "Amount to reclaim from NL (HV) for values that didn't stay in NL"),
            (" ", " ", " "),
            ("OSS import VAT paid", hv_oss_import_vat, "Total import VAT paid for HV consignments"),
            ("OSS return VAT", hv_oss_return_vat, "Total VAT to return for HV consignments (non-NL)"),
            ("NET OSS VAT", hv_oss_import_vat - hv_oss_return_vat, "Net OSS VAT to pay"),
            (" ", " ", " "),
            ("Total VAT Refund (Returns)", total_vat_refund, "Total VAT refunded for returned parcels"),
            ("Total Duty Returned", total_duty_returned, "Total refunded duty"),
            ("Total Refunds", total_duty_returned + total_vat_refund, "Total VAT + Duty refunds"),
            (" ", " ", " "),
            ("Duty Refunds Commission", dr_revenue, "DR revenue from refunds"),
            (" ", " ", " "),
            ("Amount to invoice Pro Carrier:", invoice_amount, "Net IOSS + Net OSS - HV NL returns + Commission"),
            ("Amount to be paid to Pro Carrier:", pc_return_amount, "Refunds from customs (Duty only) + reclaimed broker's money"),
        ]

        summary_df = pd.DataFrame(rows, columns=["Section", "Amount", "Description"])

        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)
        summary_df.to_excel(data_dir / "INFORMATION.xlsx", index=False, engine='openpyxl')



    @staticmethod
    def calculate_lv_data(vat_per_country_df: pd.DataFrame, return_vat_per_country_df: pd.DataFrame) -> tuple:
        """Calculate total IOSS sales and VAT to return from LV data."""
        total_ioss_vat = vat_per_country_df['Total VAT to Pay'].sum()
        returned_ioss_vat = return_vat_per_country_df['Total VAT Refund'].sum()

        return total_ioss_vat, returned_ioss_vat

    @staticmethod
    def calculate_nl_vat_returns(combined_refunds_df: pd.DataFrame) -> float:
        """Calculate total VAT returns for NL from combined refunds data."""
        nl_refunds = combined_refunds_df[combined_refunds_df['Country'] == 'NL']
        total_nl_vat_returns = nl_refunds['Total VAT Refund'].sum()

        return total_nl_vat_returns

    @staticmethod
    def calculate_oss_vat_payment(hv_vat_per_country: pd.DataFrame) -> float:
        """Calculate total VAT returns for NL from combined refunds data."""
        total_nl_vat_returns = hv_vat_per_country['Total VAT to Pay'].sum()

        return total_nl_vat_returns

    @staticmethod
    def calculate_oss_vat_returns(combined_refunds_df: pd.DataFrame) -> float:
        """Calculate total VAT returns for NL from combined refunds data."""
        nl_refunds = combined_refunds_df[combined_refunds_df['Country'] != 'NL']
        total_nl_vat_returns = nl_refunds['Total VAT Refund'].sum()

        return total_nl_vat_returns