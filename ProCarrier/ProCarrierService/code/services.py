"""Shared services for VAT calculations and data storage."""

import pandas as pd
from pathlib import Path
from ProCarrier.ProCarrierService.code.config import Config

import warnings

warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


class Services:
    """Shared service methods used across processors."""

    @staticmethod
    def store_lv_data(lv_vat_per_country) -> None:
        """Save low value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        lv_vat_per_country.to_excel(data_dir / "lv_vat_per_country_summary.xlsx", index=False,
                                    engine='openpyxl')

    @staticmethod
    def store_hv_data(hv_vat_per_country, combined_refunds) -> None:
        """Save high value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        combined_refunds.to_excel(data_dir / "HV_EU_REFUNDS.xlsx", index=False, engine='openpyxl')
        hv_vat_per_country.to_excel(data_dir / "OSS_VAT_PER_COUNTRY.xlsx", index=False, engine='openpyxl')

    @staticmethod
    def store_ie_hv_data(combined_refunds) -> None:
        """Save high value consignment data to Excel files."""
        # Create data directory if it doesn't exist
        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)

        # Save all dataframes to Excel format
        combined_refunds.to_excel(data_dir / "HV_IE_REFUNDS.xlsx", index=False, engine='openpyxl')


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
    def generate_summary_table(data: dict):
        # Calculate VAT RETURN components
        ioss_sales, ioss_vat_to_return = data['LV_VAT_DF']['Total VAT to Pay'].sum(), data['LV_VAT_DF']['Total VAT Refund'].sum()
        net_ioss = ioss_sales - ioss_vat_to_return

        # BROKER TRANSACTIONS IN NL
        value_broker_paid_during_import = data['VAT_PAID_DURING_IMPORT_TO_NL']
        value_to_return_from_nl_for_import = data['VAT_TO_RETURN_FROM_NL_FOR_IMPORT']


        #HV OSS VAT components
        hv_oss_import_vat = data['OSS_HV_VAT_DF']['Total VAT to Pay'].sum()
        hv_oss_return_vat = data['OSS_HV_VAT_DF']['Total VAT Refund'].sum()
        net_oss = hv_oss_import_vat - hv_oss_return_vat

        # HV VAT RETURNS
        nl_vat_returns = data['NL_REFUNDS']['Total VAT Refund'].sum()
        nl_duty_returns = data['NL_REFUNDS']['Total Duty Returned'].sum()
        ie_vat_returns = data['IE_REFUNDS']['Total VAT Refund'].sum()

        # DUTY REFUNDS COMMISSION
        dr_fee = ( ( nl_duty_returns + nl_vat_returns ) * 0.2 ) + ( ie_vat_returns * 0.3 )


        # Pro Carrier PAYS YOU:
        # 1. Net IOSS VAT (you pay on their behalf)
        # 2. Net OSS VAT (you pay on their behalf)
        # 3. Your commission
        invoice_amount = (
                net_ioss +  # Net IOSS
                net_oss +  # Net OSS
                dr_fee  # Commission
        )

        # DR PAY BACK to Pro Carrier:
        # We also need to return reclaimed from broker's payment VAT for HV NL returns
        pc_return_amount = nl_duty_returns + ie_vat_returns + nl_vat_returns + value_to_return_from_nl_for_import

        rows = [
            ("TOTAL IOSS VAT", ioss_sales, "Total IOSS VAT for sales"),
            ("RETURNED IOSS VAT", ioss_vat_to_return, "IOSS VAT for returns"),
            ("NET IOSS VAT", net_ioss, "Net IOSS position"),
            (" ", " ", " "),
            ("AMOUNT BROKER PAID", value_broker_paid_during_import, "VAT paid by broker during import in NL for HV"),
            ("AMOUNT THAT CAN BE CLAIMED BACK", value_to_return_from_nl_for_import, "Amount to reclaim from NL (HV) for values that didn't stay in NL"),
            (" ", " ", " "),
            ("OSS import VAT paid", hv_oss_import_vat, "Total import VAT paid for HV consignments"),
            ("OSS return VAT", hv_oss_return_vat, "Total VAT to return for HV consignments (non-NL)"),
            ("NET OSS VAT", net_oss, "Net OSS VAT to pay"),
            (" ", " ", " "),
            ("Total VAT Refund From HV", ie_vat_returns + nl_vat_returns, "Total VAT refunded for returned HV parcels "),
            ("Total Duty Returned", nl_duty_returns, "Total refunded duty"),
            ("Total Refunds", nl_duty_returns + ie_vat_returns + nl_vat_returns, "Total VAT + Duty refunds"),
            (" ", " ", " "),
            ("Duty Refunds Commission", dr_fee, "DR revenue from refunds"),
            (" ", " ", " "),
            ("Amount to invoice Pro Carrier:", invoice_amount, "Net IOSS + Net OSS + Commission"),
            ("Amount to be paid to Pro Carrier:", pc_return_amount, "Refunds from customs + reclaimed broker's money"),
        ]

        summary_df = pd.DataFrame(rows, columns=["Section", "Amount", "Description"])

        data_dir = Path(Config.DATA_DIR)
        data_dir.mkdir(exist_ok=True)
        summary_df.to_excel(data_dir / "INFORMATION.xlsx", index=False, engine='openpyxl')

